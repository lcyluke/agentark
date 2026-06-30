"""
UAT: Apex-Hermes Bridge Integration
══════════════════════════════════════
QA Agent validates:
  1. bridge init creates 6 agents
  2. bridge sync updates Kanban from state.db
  3. bridge status returns health
  4. web API endpoints respond
  5. CLI commands work
"""

import json
import os
import sys
import tempfile
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "apex"))

# Use temp dir for isolated tests
TEST_HOME = Path(tempfile.mkdtemp(prefix="apex_bridge_uat_"))
TEST_HOME.mkdir(parents=True, exist_ok=True)
os.environ["AGENTARK_HOME"] = str(TEST_HOME)


class TestBridgeInit:
    """TC-BRIDGE-01: Bridge agent creation"""

    def test_init_creates_6_agents(self):
        from agentark.cli.commands.bridge import init_bridge_agents, BRIDGE_AGENTS
        result = init_bridge_agents()
        assert len(result["created"]) + len(result["updated"]) >= 6
        assert len(BRIDGE_AGENTS) >= 7  # 6 bridge + origin

    def test_agents_persist_to_profiles(self):
        from agentark.core.profile import ProfileManager
        pm = ProfileManager()
        profiles = pm.list()
        bridge_names = {"origin", "fleet-commander", "session-scout", "token-guardian",
                        "gpu-sentinel", "profile-syncer", "cron-medic"}
        assert bridge_names.issubset(set(profiles))

    def test_agent_roles_defined(self):
        from agentark.core.profile import ProfileManager
        from agentark.cli.commands.bridge import BRIDGE_AGENTS
        pm = ProfileManager()
        for name, cfg in BRIDGE_AGENTS.items():
            p = pm.load(name)
            assert p.soul.role == cfg["role"]
            assert p.soul.expertise == cfg["expertise"]
            assert p.skills == cfg["skills"]
            assert p.auto_improve is True


class TestBridgeSync:
    """TC-BRIDGE-02: Sync engine"""

    def test_sync_creates_kanban_tasks(self):
        from agentark.cli.commands.bridge import run_bridge_sync
        from agentark.orchestration.kanban import Kanban
        from agentark.core.profile import AGENTARK_HOME

        status = run_bridge_sync()

        # Verify Kanban tasks created
        k = Kanban(AGENTARK_HOME / "kanban.db")
        tasks = {t.id: t for t in k.list_tasks()}

        expected = {"watch-sessions", "watch-tokens", "watch-gpu",
                     "watch-profiles", "watch-cron", "fleet-status"}
        assert expected.issubset(set(tasks.keys()))

        # Verify each task has an assignee from the bridge fleet
        for tid in expected:
            t = tasks[tid]
            assert t.assignee in ("session-scout", "token-guardian", "gpu-sentinel",
                                   "profile-syncer", "cron-medic", "fleet-commander")

    def test_sync_produces_output(self):
        from agentark.cli.commands.bridge import run_bridge_sync
        from agentark.orchestration.kanban import Kanban
        from agentark.core.profile import AGENTARK_HOME

        run_bridge_sync()
        k = Kanban(AGENTARK_HOME / "kanban.db")
        fleet = k.get_task("fleet-status")
        assert fleet is not None
        assert fleet.output and len(fleet.output) > 10


class TestBridgeStatus:
    """TC-BRIDGE-03: Status reporting"""

    def test_get_bridge_status(self):
        from agentark.cli.commands.bridge import get_bridge_status
        status = get_bridge_status()
        assert status["status"] in ("healthy", "degraded", "offline")
        assert "agents" in status
        assert "total" in status
        assert "healthy" in status

    def test_agents_have_status_fields(self):
        from agentark.cli.commands.bridge import get_bridge_status
        status = get_bridge_status()
        for agent in status["agents"]:
            assert "id" in agent
            assert "assignee" in agent
            assert "status" in agent
            assert agent["status"] in ("done", "in_progress", "blocked", "todo")


class TestBridgeWebAPI:
    """TC-BRIDGE-04: Dashboard REST endpoints"""
    import os

    @pytest.fixture(autouse=True)
    def setup_app(self):
        pytest.importorskip("flask", reason="Flask not installed in this Python")
        os.environ["AGENTARK_HOME"] = str(TEST_HOME)
        from agentark.cli.commands.bridge import init_bridge_agents, run_bridge_sync
        init_bridge_agents()
        run_bridge_sync()

    def test_api_bridge_status(self):
        from agentark.interface.web import create_app
        app = create_app()
        client = app.test_client()
        resp = client.get("/api/bridge/status")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "agents" in data
        assert "total" in data

    def test_api_bridge_sync(self):
        from agentark.interface.web import create_app
        app = create_app()
        client = app.test_client()
        resp = client.post("/api/bridge/sync")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["status"] in ("healthy", "degraded", "offline")

    def test_api_bridge_init(self):
        from agentark.interface.web import create_app
        app = create_app()
        client = app.test_client()
        resp = client.post("/api/bridge/init")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "created" in data or "updated" in data


class TestBridgeCLI:
    """TC-BRIDGE-05: CLI commands"""

    def test_bridge_init_cli(self):
        from agentark.cli.commands.bridge import init_bridge_agents
        result = init_bridge_agents()
        assert isinstance(result, dict)
        assert "created" in result
        assert "updated" in result

    def test_bridge_status_cli(self):
        from agentark.cli.commands.bridge import get_bridge_status
        status = get_bridge_status()
        assert isinstance(status, dict)
        assert "agents" in status
