/**
 * apex-client.ts — JSON-line client for communicating with apexd.
 *
 * Connects via Unix domain socket at ~/.apex/apexd.sock (design spec),
 * falling back to ~/.apex/agentops.sock (actual daemon), and finally
 * TCP at 127.0.0.1:8717.
 */

import * as net from "node:net";
import * as fs from "node:fs";
import * as path from "node:path";
import * as os from "node:os";

// ── Types ────────────────────────────────────────────────────────────────────

export interface ApexRequest {
  id: string;
  command: string;
  session_id?: string;
  payload?: Record<string, unknown>;
}

export interface ApexResponse {
  id: string;
  command: string;
  session_id: string;
  ok: boolean;
  data: Record<string, unknown>;
  error: string;
  timestamp: string;
}

// ── Connection targets ───────────────────────────────────────────────────────

const APEX_HOME = process.env["APEX_HOME"] || path.join(os.homedir(), ".apex");

const SOCKET_PATHS = [
  path.join(APEX_HOME, "apexd.sock"),      // design spec (§9.5)
  path.join(APEX_HOME, "agentops.sock"),    // actual daemon
];

const TCP_HOST = process.env["APEX_HOST"] || "127.0.0.1";
const TCP_PORT = parseInt(process.env["APEX_PORT"] || "8717", 10);

// ── Low-level socket send/receive ────────────────────────────────────────────

function connectUnix(socketPath: string, timeoutMs: number): Promise<net.Socket> {
  return new Promise((resolve, reject) => {
    const sock = new net.Socket();
    const timer = setTimeout(() => {
      sock.destroy();
      reject(new Error(`connect timeout: ${socketPath}`));
    }, timeoutMs);

    sock.once("connect", () => {
      clearTimeout(timer);
      resolve(sock);
    });
    sock.once("error", (err) => {
      clearTimeout(timer);
      reject(err);
    });
    sock.connect({ path: socketPath });
  });
}

function connectTcp(host: string, port: number, timeoutMs: number): Promise<net.Socket> {
  return new Promise((resolve, reject) => {
    const sock = new net.Socket();
    const timer = setTimeout(() => {
      sock.destroy();
      reject(new Error(`connect timeout: ${host}:${port}`));
    }, timeoutMs);

    sock.once("connect", () => {
      clearTimeout(timer);
      resolve(sock);
    });
    sock.once("error", (err) => {
      clearTimeout(timer);
      reject(err);
    });
    sock.connect(port, host);
  });
}

function sendReceive(sock: net.Socket, request: ApexRequest, timeoutMs: number): Promise<ApexResponse> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      sock.destroy();
      reject(new Error(`request timeout: ${request.command}`));
    }, timeoutMs);

    const chunks: Buffer[] = [];

    sock.once("data", (data: Buffer) => {
      chunks.push(data);
      // Try to parse immediately if we have a full line
      const buf = Buffer.concat(chunks);
      const newlineIdx = buf.indexOf("\n");
      if (newlineIdx >= 0) {
        clearTimeout(timer);
        const line = buf.subarray(0, newlineIdx).toString("utf-8").trim();
        try {
          const response = JSON.parse(line) as ApexResponse;
          resolve(response);
        } catch (err) {
          reject(new Error(`invalid JSON response: ${line.slice(0, 200)}`));
        }
      } else {
        // Need more data — listen for more
        sock.once("data", (more: Buffer) => {
          chunks.push(more);
          const buf2 = Buffer.concat(chunks);
          const idx = buf2.indexOf("\n");
          if (idx >= 0) {
            clearTimeout(timer);
            const line = buf2.subarray(0, idx).toString("utf-8").trim();
            try {
              const response = JSON.parse(line) as ApexResponse;
              resolve(response);
            } catch (err) {
              reject(new Error(`invalid JSON response: ${line.slice(0, 200)}`));
            }
          } else {
            clearTimeout(timer);
            reject(new Error("incomplete response (no newline)"));
          }
        });
      }
    });

    sock.once("error", (err) => {
      clearTimeout(timer);
      reject(err);
    });

    sock.once("close", () => {
      clearTimeout(timer);
      if (chunks.length > 0) {
        // Already resolved or will resolve via data handler
        return;
      }
      reject(new Error("connection closed before response"));
    });

    const payload = JSON.stringify(request) + "\n";
    sock.write(payload);
  });
}

// ── Public API ───────────────────────────────────────────────────────────────

let _cachedSocket: net.Socket | null = null;
let _cachedTarget: string | null = null;

export interface ApexClientOptions {
  timeout?: number;  // per-request timeout ms (default: 10000)
}

export class ApexClient {
  private timeout: number;

  constructor(options: ApexClientOptions = {}) {
    this.timeout = options.timeout || 10000;
  }

  /**
   * Connect to apexd, trying socket paths then TCP fallback.
   * Returns connected socket. Reuses cached connection if alive.
   */
  async connect(): Promise<{ sock: net.Socket; target: string }> {
    if (_cachedSocket && !_cachedSocket.destroyed) {
      return { sock: _cachedSocket, target: _cachedTarget || "cached" };
    }

    // Try Unix sockets first
    for (const socketPath of SOCKET_PATHS) {
      if (!fs.existsSync(socketPath)) continue;
      try {
        const sock = await connectUnix(socketPath, this.timeout);
        _cachedSocket = sock;
        _cachedTarget = socketPath;
        return { sock, target: socketPath };
      } catch {
        // Try next
      }
    }

    // Fallback to TCP
    try {
      const sock = await connectTcp(TCP_HOST, TCP_PORT, this.timeout);
      _cachedSocket = sock;
      _cachedTarget = `${TCP_HOST}:${TCP_PORT}`;
      return { sock, target: `${TCP_HOST}:${TCP_PORT}` };
    } catch {
      throw new Error(
        `Cannot connect to apexd via any path (tried ${SOCKET_PATHS.join(", ")}, ` +
        `and TCP ${TCP_HOST}:${TCP_PORT}). Is the daemon running?`
      );
    }
  }

  /** Send a command and return the response. */
  async send(command: string, sessionId?: string, payload?: Record<string, unknown>): Promise<ApexResponse> {
    const { sock } = await this.connect();

    const request: ApexRequest = {
      id: crypto.randomUUID(),
      command,
      session_id: sessionId || "",
      payload: payload || {},
    };

    const response = await sendReceive(sock, request, this.timeout);

    // If the socket was closed by the server, reset cache
    if (sock.destroyed) {
      _cachedSocket = null;
      _cachedTarget = null;
    }

    return response;
  }

  /** Close the persistent connection. */
  close(): void {
    if (_cachedSocket && !_cachedSocket.destroyed) {
      _cachedSocket.destroy();
    }
    _cachedSocket = null;
    _cachedTarget = null;
  }

  /** Test connectivity — returns connected target or throws. */
  async ping(): Promise<string> {
    const { target } = await this.connect();
    return target;
  }
}

/** Default singleton client */
export const apexClient = new ApexClient();
