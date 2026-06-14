/**
 * index.ts — MCP server for APEX operations (§9.5).
 *
 * Provides 6 tools via stdio transport:
 *   apex_spawn, apex_status, apex_blackboard, apex_claims, apex_stop, apex_doctor
 *
 * Talks to apexd via Unix socket (preferred) or TCP fallback.
 * Blackboard and claims data are read directly from the SQLite DB
 * at ~/.apex/agentops.db (with socket-based forwarding as future path).
 */

import * as os from "node:os";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

import { ApexClient, apexClient } from "./apex-client.js";
import { BlackboardAccessor } from "./db-access.js";
import { ClaimsAccessor } from "./db-access.js";

// ── Initialize ───────────────────────────────────────────────────────────────

const server = new McpServer({
  name: "apex-ops-mcp",
  version: "1.0.0",
});

const dbBlackboard = new BlackboardAccessor();
const dbClaims = new ClaimsAccessor();

// ── Helper: format response for MCP tool result ──────────────────────────────

function formatResult(data: unknown): { content: Array<{ type: "text"; text: string }> } {
  const text = typeof data === "string" ? data : JSON.stringify(data, null, 2);
  return { content: [{ type: "text", text }] };
}

// ═══════════════════════════════════════════════════════════════════════════════
// Tool: apex_spawn
// ═══════════════════════════════════════════════════════════════════════════════

server.tool(
  "apex_spawn",
  "Spawn a new APEX agent session. Returns the session_id for tracking.",
  {
    agent: z.string().describe("Agent name or profile to spawn"),
    task: z.string().describe("Task description / prompt for the agent"),
    cwd: z.string().optional().describe("Working directory (optional)"),
  },
  async ({ agent, task, cwd }) => {
    const payload: Record<string, unknown> = {
      agent,
      text: task,
      profile: agent,
    };
    if (cwd) payload["cwd"] = cwd;

    try {
      const response = await apexClient.send("spawn", undefined, payload);
      if (response.ok) {
        return formatResult({
          success: true,
          session_id: response.data["session_id"],
          agent: response.data["agent"] || agent,
          profile: response.data["profile"] || agent,
          timestamp: response.timestamp,
        });
      } else {
        return formatResult({
          success: false,
          error: response.error || "spawn failed",
        });
      }
    } catch (err) {
      return formatResult({
        success: false,
        error: err instanceof Error ? err.message : String(err),
      });
    }
  }
);

// ═══════════════════════════════════════════════════════════════════════════════
// Tool: apex_status
// ═══════════════════════════════════════════════════════════════════════════════

server.tool(
  "apex_status",
  "Query status of an APEX session, or list all sessions if no session_id given.",
  {
    session_id: z.string().optional().describe("Session ID to query (omit for list-all)"),
  },
  async ({ session_id }) => {
    try {
      const response = await apexClient.send("status", session_id || undefined);
      if (response.ok) {
        return formatResult({
          success: true,
          data: response.data,
          timestamp: response.timestamp,
        });
      } else {
        return formatResult({
          success: false,
          error: response.error || "status query failed",
        });
      }
    } catch (err) {
      return formatResult({
        success: false,
        error: err instanceof Error ? err.message : String(err),
        hint: "Is apexd running? Try apex_doctor to diagnose.",
      });
    }
  }
);

// ═══════════════════════════════════════════════════════════════════════════════
// Tool: apex_blackboard
// ═══════════════════════════════════════════════════════════════════════════════

server.tool(
  "apex_blackboard",
  "Search the shared APEX blackboard for cross-agent knowledge. " +
  "Pass a query string to search conclusions; omit to get recent entries.",
  {
    query: z.string().describe("Search term (matched against conclusion text). Use '*' for all."),
    filter_author: z.string().optional().describe("Filter by author name"),
    verified_only: z.boolean().optional().default(false).describe("Only return Auditor-verified entries"),
    limit: z.number().optional().default(50).describe("Max results (1-200)"),
  },
  async ({ query, filter_author, verified_only, limit }) => {
    try {
      const what = query === "*" ? "" : query;
      const clampedLimit = Math.min(Math.max(limit || 50, 1), 200);
      const results = dbBlackboard.query({
        what,
        filterAuthor: filter_author || undefined,
        verifiedOnly: verified_only || false,
        limit: clampedLimit,
      });

      return formatResult({
        success: true,
        count: results.length,
        query: query,
        entries: results,
      });
    } catch (err) {
      return formatResult({
        success: false,
        error: err instanceof Error ? err.message : String(err),
        hint: "Blackboard reads directly from ~/.apex/agentops.db — ensure APEX_HOME is set correctly.",
      });
    }
  }
);

// ═══════════════════════════════════════════════════════════════════════════════
// Tool: apex_claims
// ═══════════════════════════════════════════════════════════════════════════════

server.tool(
  "apex_claims",
  "List active claims in the APEX claims registry. Shows which tasks are claimed, " +
  "by whom, and when.",
  {
    status: z.string().optional().describe("Filter by status ('active', 'completed', etc.). Default: 'active'"),
    claimed_by: z.string().optional().describe("Filter by claim holder name"),
    limit: z.number().optional().default(50).describe("Max results (1-200)"),
  },
  async ({ status, claimed_by, limit }) => {
    try {
      const clampedLimit = Math.min(Math.max(limit || 50, 1), 200);
      const results = dbClaims.query({
        status: status || "active",
        claimedBy: claimed_by || undefined,
        limit: clampedLimit,
      });

      return formatResult({
        success: true,
        count: results.length,
        claims: results,
      });
    } catch (err) {
      return formatResult({
        success: false,
        error: err instanceof Error ? err.message : String(err),
        hint: "Claims read directly from ~/.apex/agentops.db — ensure APEX_HOME is set correctly.",
      });
    }
  }
);

// ═══════════════════════════════════════════════════════════════════════════════
// Tool: apex_stop
// ═══════════════════════════════════════════════════════════════════════════════

server.tool(
  "apex_stop",
  "Stop (dispose) an APEX agent session. This terminates the session and releases resources.",
  {
    session_id: z.string().describe("Session ID to stop/dispose"),
  },
  async ({ session_id }) => {
    try {
      const response = await apexClient.send("dispose", session_id);
      if (response.ok) {
        return formatResult({
          success: true,
          session_id: session_id,
          disposed: response.data["disposed"] || true,
          timestamp: response.timestamp,
        });
      } else {
        return formatResult({
          success: false,
          session_id: session_id,
          error: response.error || "dispose failed",
        });
      }
    } catch (err) {
      return formatResult({
        success: false,
        error: err instanceof Error ? err.message : String(err),
      });
    }
  }
);

// ═══════════════════════════════════════════════════════════════════════════════
// Tool: apex_doctor
// ═══════════════════════════════════════════════════════════════════════════════

server.tool(
  "apex_doctor",
  "Run health checks on the APEX infrastructure. Tests socket connectivity, " +
  "database accessibility, and reports configuration.",
  {},
  async () => {
    const results: Record<string, unknown> = {
      timestamp: new Date().toISOString(),
      checks: {} as Record<string, unknown>,
    };

    // Check 1: Socket connectivity
    try {
      const target = await apexClient.ping();
      results["checks"]["socket"] = {
        status: "ok",
        target,
      };
    } catch (err) {
      results["checks"]["socket"] = {
        status: "error",
        message: err instanceof Error ? err.message : String(err),
      };
    }

    // Check 2: DB accessibility (blackboard)
    try {
      const bbCount = dbBlackboard.count();
      results["checks"]["blackboard_db"] = {
        status: "ok",
        entries: bbCount,
        path: dbBlackboard.dbPath,
      };
    } catch (err) {
      results["checks"]["blackboard_db"] = {
        status: "error",
        message: err instanceof Error ? err.message : String(err),
      };
    }

    // Check 3: DB accessibility (claims)
    try {
      const claimsCount = dbClaims.count();
      results["checks"]["claims_db"] = {
        status: "ok",
        entries: claimsCount,
        path: dbClaims.dbPath,
      };
    } catch (err) {
      results["checks"]["claims_db"] = {
        status: "error",
        message: err instanceof Error ? err.message : String(err),
      };
    }

    // Check 4: APEX_HOME
    const apexHome = process.env["APEX_HOME"] || os.homedir() + "/.apex";
    results["checks"]["apex_home"] = {
      status: "info",
      path: apexHome,
    };

    // Overall status
    const checks = results["checks"] as Record<string, { status: string }>;
    const allOk = Object.values(checks).every((c) => c.status !== "error");
    results["healthy"] = allOk;

    return formatResult(results);
  }
);

// ── Main ─────────────────────────────────────────────────────────────────────

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);

  // Log to stderr so it doesn't interfere with stdio MCP protocol
  const apexHome = process.env["APEX_HOME"] || os.homedir() + "/.apex";
  console.error(`[apex-ops-mcp] started (APEX_HOME=${apexHome})`);

  // Graceful shutdown
  process.on("SIGINT", () => {
    console.error("[apex-ops-mcp] shutting down...");
    apexClient.close();
    dbBlackboard.close();
    dbClaims.close();
    process.exit(0);
  });
  process.on("SIGTERM", () => {
    console.error("[apex-ops-mcp] shutting down...");
    apexClient.close();
    dbBlackboard.close();
    dbClaims.close();
    process.exit(0);
  });
}

main().catch((err) => {
  console.error(`[apex-ops-mcp] fatal: ${err.message}`);
  process.exit(1);
});
