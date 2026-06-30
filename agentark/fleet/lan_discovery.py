"""
LAN Node Discovery — mDNS + SSH Local Fleet Backbone
═══════════════════════════════════════════════════════
Replaces GitHub-only sync with LAN-first connectivity.

Architecture:
  1. mDNS (Bonjour) service broadcast: each Mac advertises
     _agentark-fleet._tcp on the local network
  2. SSH key-based connectivity check between peers
  3. Local heartbeat file (shared via fleet/nodes/ on git)
     but with LAN fallback — direct SSH when GitHub is slow/unavailable
  4. Peer discovery + auto-registration

Protocol:
  - Service type: _agentark-fleet._tcp
  - TXT records: machine_id, role, hostname, port, profiles, has_gpu
  - Heartbeat interval: configurable (default 30s)

Requirements:
  pip install zeroconf  (python-zeroconf)

Integration:
  from agentark.fleet.lan_discovery import LANFleetDiscovery
  lan = LANFleetDiscovery()
  lan.start()   # starts mDNS broadcast + listener
  peers = lan.discover_peers()  # returns list of LAN peers
  lan.connect_peer(peer)  # SSH connectivity test
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Callable

# ─── Service constants ────────────────────────────────────────
SERVICE_TYPE = "_agentark-fleet._tcp.local."
DEFAULT_PORT = 9922  # Arbitrary non-privileged port for fleet protocol
LAN_PEERS_FILE = Path(os.path.expanduser("~/.apex/lan_peers.json"))
SSH_TIMEOUT = 5  # seconds for SSH connectivity test


@dataclass
class LANPeer:
    """A fleet node discovered on the LAN."""
    machine_id: str
    hostname: str
    role: str              # "origin" or "worker"
    ip_address: str
    port: int = DEFAULT_PORT
    profiles: int = 0
    skills: int = 0
    has_gpu: bool = False
    gpu_names: list[str] = field(default_factory=list)
    last_seen: float = 0.0
    ssh_reachable: bool = False
    latency_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "machine_id": self.machine_id,
            "hostname": self.hostname,
            "role": self.role,
            "ip_address": self.ip_address,
            "port": self.port,
            "profiles": self.profiles,
            "skills": self.skills,
            "has_gpu": self.has_gpu,
            "gpu_names": self.gpu_names,
            "last_seen": self.last_seen,
            "ssh_reachable": self.ssh_reachable,
            "latency_ms": self.latency_ms,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "LANPeer":
        return cls(**{k: d.get(k) for k in [
            "machine_id", "hostname", "role", "ip_address", "port",
            "profiles", "skills", "has_gpu", "gpu_names",
            "last_seen", "ssh_reachable", "latency_ms",
        ] if k in d})


# ═══════════════════════════════════════════════════════════════
# LAN Fleet Discovery Engine
# ═══════════════════════════════════════════════════════════════

class LANFleetDiscovery:
    """mDNS-based LAN peer discovery for AgentArk fleet.

    Usage:
        lan = LANFleetDiscovery()
        lan.start()                    # background: broadcast + listen
        time.sleep(3)                  # wait for discovery
        peers = lan.discover_peers()   # get active LAN peers
        lan.stop()
    """

    def __init__(
        self,
        machine_id: Optional[str] = None,
        role: str = "origin",
        port: int = DEFAULT_PORT,
        service_name: Optional[str] = None,
    ):
        self.machine_id = machine_id or self._get_machine_id()
        self.hostname = socket.gethostname()
        self.role = role
        self.port = port
        # Sanitize machine_id for mDNS — replace dots to avoid parsing issues
        safe_id = self.machine_id.replace(".", "-")
        self.service_name = service_name or f"{safe_id}.{SERVICE_TYPE}"
        self._running = False
        self._zeroconf = None
        self._service_info = None
        self._browser = None
        self._lock = threading.Lock()
        self._peers: dict[str, LANPeer] = {}
        self._on_peer_discovered: Optional[Callable] = None
        self._on_peer_lost: Optional[Callable] = None

    # ─── Identity ─────────────────────────────────────────────

    @staticmethod
    def _get_machine_id() -> str:
        """Stable machine identifier."""
        hostname = socket.gethostname()
        try:
            username = os.getlogin()
        except Exception:
            username = os.environ.get("USER", "unknown")
        return f"{hostname}-{username}"

    @staticmethod
    def _get_local_ip() -> str:
        """Get the primary LAN IP address."""
        try:
            # Connect to an external address to determine primary interface
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(1)
            s.connect(("8.8.8.8", 80))  # Doesn't actually send data
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    # ─── GPU Probe ────────────────────────────────────────────

    @staticmethod
    def probe_gpu() -> dict:
        """Check if this machine has NVIDIA GPU via nvidia-smi."""
        try:
            r = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=5,
            )
            if r.returncode == 0 and r.stdout.strip():
                names = [n.strip() for n in r.stdout.strip().split("\n")]
                return {"has_gpu": True, "gpu_names": names}
        except Exception:
            pass
        return {"has_gpu": False, "gpu_names": []}

    # ─── Public API ───────────────────────────────────────────

    def start(self, on_peer_discovered: Optional[Callable] = None,
              on_peer_lost: Optional[Callable] = None):
        """Start mDNS advertisement + browser in background thread.

        Args:
            on_peer_discovered: callback(peer: LANPeer) when a peer is found
            on_peer_lost: callback(peer: LANPeer) when a peer disappears
        """
        if self._running:
            return

        self._on_peer_discovered = on_peer_discovered
        self._on_peer_lost = on_peer_lost
        self._running = True

        thread = threading.Thread(target=self._run_loop, daemon=True, name="lan-fleet")
        thread.start()

    def stop(self):
        """Stop mDNS services."""
        self._running = False
        if self._zeroconf:
            try:
                if self._browser:
                    self._zeroconf.remove_service_listener(self._browser)
                if self._service_info:
                    self._zeroconf.unregister_service(self._service_info)
                self._zeroconf.close()
            except Exception:
                pass
            self._zeroconf = None

    def discover_peers(self, test_ssh: bool = True) -> list[LANPeer]:
        """Get all currently known LAN peers.

        Args:
            test_ssh: If True, run SSH connectivity check on each peer

        Returns:
            List of LANPeer objects (excluding self)
        """
        with self._lock:
            peers = [p for mid, p in self._peers.items()
                     if mid != self.machine_id]

        if test_ssh:
            for peer in peers:
                peer.ssh_reachable, peer.latency_ms = self._test_ssh(peer)

        return peers

    def find_peer(self, machine_id: str) -> Optional[LANPeer]:
        """Find a specific peer by machine_id."""
        with self._lock:
            return self._peers.get(machine_id)

    @property
    def peer_count(self) -> int:
        with self._lock:
            return len(self._peers)

    def save_peers(self):
        """Persist discovered peers to disk for offline lookup."""
        with self._lock:
            data = {
                "updated_at": time.time(),
                "peers": {mid: p.to_dict() for mid, p in self._peers.items()},
            }
        LAN_PEERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        LAN_PEERS_FILE.write_text(json.dumps(data, indent=2))

    def load_peers(self) -> list[LANPeer]:
        """Load previously saved peers from disk."""
        if not LAN_PEERS_FILE.exists():
            return []
        try:
            data = json.loads(LAN_PEERS_FILE.read_text())
            return [LANPeer.from_dict(p) for p in data.get("peers", {}).values()]
        except Exception:
            return []

    # ─── SSH Connectivity ─────────────────────────────────────

    @staticmethod
    def _test_ssh(peer: LANPeer) -> tuple[bool, float]:
        """Test SSH connectivity to a peer. Returns (reachable, latency_ms)."""
        try:
            start = time.monotonic()
            r = subprocess.run(
                ["ssh", "-o", "ConnectTimeout=3",
                 "-o", "StrictHostKeyChecking=accept-new",
                 "-o", "BatchMode=yes",
                 peer.hostname, "echo", "pong"],
                capture_output=True, timeout=SSH_TIMEOUT + 2,
            )
            latency = (time.monotonic() - start) * 1000
            return (r.returncode == 0 and "pong" in r.stdout.decode()), latency
        except Exception:
            return False, 0.0

    @staticmethod
    def ssh_exec(hostname: str, command: str, timeout: int = 30) -> tuple[bool, str]:
        """Execute a command on a remote peer via SSH.

        Returns:
            (success, output)
        """
        try:
            r = subprocess.run(
                ["ssh", "-o", "ConnectTimeout=5",
                 "-o", "StrictHostKeyChecking=accept-new",
                 "-o", "BatchMode=yes",
                 hostname, command],
                capture_output=True, text=True, timeout=timeout,
            )
            return r.returncode == 0, r.stdout + r.stderr
        except Exception as e:
            return False, str(e)

    @staticmethod
    def ssh_dispatch_task(hostname: str, task: str, profile: Optional[str] = None,
                          timeout: int = 600) -> tuple[bool, str]:
        """Dispatch a task to a peer via SSH + hermes.

        Args:
            hostname: target hostname
            task: the task description/prompt
            profile: Hermes profile name (optional)
            timeout: seconds to wait

        Returns:
            (success, output)
        """
        if profile:
            cmd = f"hermes -p {profile} chat -q {_shquote(task)}"
        else:
            cmd = f"hermes chat -q {_shquote(task)}"

        try:
            r = subprocess.run(
                ["ssh", "-o", "ConnectTimeout=5",
                 "-o", "StrictHostKeyChecking=accept-new",
                 "-o", "BatchMode=yes",
                 hostname, cmd],
                capture_output=True, text=True, timeout=timeout,
            )
            ok = r.returncode == 0
            return ok, r.stdout if ok else r.stderr
        except subprocess.TimeoutExpired:
            return False, f"Task timed out after {timeout}s"
        except Exception as e:
            return False, str(e)

    # ─── Internal: mDNS Loop ──────────────────────────────────

    def _run_loop(self):
        """Background thread: advertise + browse mDNS."""
        try:
            from zeroconf import ServiceBrowser, ServiceInfo, Zeroconf
        except ImportError:
            print("[lan_discovery] ⚠️ python-zeroconf not installed. "
                  "Run: pip install zeroconf")
            self._running = False
            return

        local_ip = self._get_local_ip()
        gpu_info = self.probe_gpu()

        # Read fleet config for profiles/skills count
        profiles = 0
        skills = 0
        try:
            from agentark.interface.fleet_multi_mac import get_fleet_config, fleet_status
            status = fleet_status()
            profiles = status.get("profiles", 0)
            skills = status.get("skills", 0)
        except Exception:
            pass

        # TXT records
        txt = {
            "machine_id": self.machine_id,
            "hostname": self.hostname,
            "role": self.role,
            "profiles": str(profiles),
            "skills": str(skills),
            "has_gpu": str(gpu_info["has_gpu"]).lower(),
            "gpu_names": ",".join(gpu_info.get("gpu_names", [])),
        }

        self._zeroconf = Zeroconf()

        # Register our service
        try:
            self._service_info = ServiceInfo(
                SERVICE_TYPE,
                self.service_name,
                addresses=[socket.inet_aton(local_ip)],
                port=self.port,
                properties=txt,
            )
            self._zeroconf.register_service(self._service_info)
        except Exception as e:
            print(f"[lan_discovery] ⚠️ Failed to register mDNS service: {e}")

        # Browse for peers
        class PeerListener:
            def __init__(self, parent: "LANFleetDiscovery"):
                self.parent = parent

            def remove_service(self, zc, service_type, name):
                # Extract machine_id from service name
                for mid, peer in list(self.parent._peers.items()):
                    svc_name = f"{mid}.{SERVICE_TYPE}"
                    if svc_name == name:
                        with self.parent._lock:
                            del self.parent._peers[mid]
                        if self.parent._on_peer_lost:
                            try:
                                self.parent._on_peer_lost(peer)
                            except Exception:
                                pass
                        break

            def add_service(self, zc, service_type, name):
                try:
                    info = zc.get_service_info(service_type, name)
                    if info is None:
                        return
                except Exception:
                    return

                props = {}
                for k, v in info.properties.items():
                    key = k.decode() if isinstance(k, bytes) else k
                    val = v.decode() if isinstance(v, bytes) else (v or "")
                    props[key] = val
                mid = props.get("machine_id", name)

                # Skip self
                if mid == self.parent.machine_id:
                    return

                ip = socket.inet_ntoa(info.addresses[0]) if info.addresses else "unknown"
                peer = LANPeer(
                    machine_id=mid,
                    hostname=props.get("hostname", "unknown"),
                    role=props.get("role", "unknown"),
                    ip_address=ip,
                    port=info.port,
                    profiles=int(props.get("profiles", 0)),
                    skills=int(props.get("skills", 0)),
                    has_gpu=props.get("has_gpu", "false") == "true",
                    gpu_names=[n for n in props.get("gpu_names", "").split(",") if n],
                    last_seen=time.time(),
                )

                # Test SSH
                peer.ssh_reachable, peer.latency_ms = self.parent._test_ssh(peer)

                with self.parent._lock:
                    self.parent._peers[mid] = peer

                if self.parent._on_peer_discovered:
                    try:
                        self.parent._on_peer_discovered(peer)
                    except Exception:
                        pass

            def update_service(self, zc, service_type, name):
                # Treat update same as add
                self.add_service(zc, service_type, name)

        self._browser = ServiceBrowser(self._zeroconf, SERVICE_TYPE,
                                        PeerListener(self))

        # Keep alive
        while self._running:
            time.sleep(1)

        # Cleanup on stop
        try:
            if self._browser:
                self._zeroconf.remove_service_listener(self._browser)
            if self._service_info:
                self._zeroconf.unregister_service(self._service_info)
            self._zeroconf.close()
        except Exception:
            pass


# ─── Utility ──────────────────────────────────────────────────

def _shquote(s: str) -> str:
    """Shell-quote a string for safe SSH command construction."""
    import shlex
    return shlex.quote(s)


# ─── Quick CLI test ───────────────────────────────────────────

def _cli_test():
    """Quick test: run on 2+ Macs to see peer discovery."""
    import sys
    role = sys.argv[1] if len(sys.argv) > 1 else "origin"

    lan = LANFleetDiscovery(role=role)

    def on_found(peer: LANPeer):
        print(f"[+] Peer found: {peer.machine_id} @ {peer.ip_address} "
              f"role={peer.role} ssh={'OK' if peer.ssh_reachable else 'NO'} "
              f"gpu={'YES' if peer.has_gpu else 'NO'}")

    def on_lost(peer: LANPeer):
        print(f"[-] Peer lost: {peer.machine_id}")

    lan.start(on_peer_discovered=on_found, on_peer_lost=on_lost)
    print(f"[*] {role} broadcasting as {lan.machine_id} on LAN...")
    print("[*] Press Ctrl+C to stop")

    try:
        while True:
            time.sleep(5)
            peers = lan.discover_peers(test_ssh=True)
            if peers:
                print(f"\n── Active peers ({len(peers)}) ──")
                for p in peers:
                    conn = f"✅ SSH {p.latency_ms:.0f}ms" if p.ssh_reachable else "❌ no SSH"
                    print(f"  {p.machine_id:30s} {p.role:8s} {conn} "
                          f"profiles={p.profiles} gpu={'🖥' if p.has_gpu else '—'}")
            lan.save_peers()
    except KeyboardInterrupt:
        print("\n[*] Stopping...")
        lan.stop()


if __name__ == "__main__":
    _cli_test()
