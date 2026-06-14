/**
 * db-access.ts — Direct SQLite access to the APEX blackboard and claims DB.
 *
 * Reads from ~/.apex/agentops.db (same SQLite DB used by apex.storage.db,
 * apex.core.blackboard, and apex.core.claims).
 *
 * Uses the built-in node:sqlite module (available in Node.js 22.5+).
 * This is a fallback for when the daemon doesn't yet expose blackboard/claims
 * commands. Future versions should route through the socket protocol.
 */

import { DatabaseSync } from "node:sqlite";
import * as path from "node:path";
import * as os from "node:os";
import * as fs from "node:fs";

// ── DB path ──────────────────────────────────────────────────────────────────

const APEX_HOME = process.env["APEX_HOME"] || path.join(os.homedir(), ".apex");
const DEFAULT_DB_PATH = process.env["APEX_DB_PATH"] || path.join(APEX_HOME, "agentops.db");

// ── Helpers ──────────────────────────────────────────────────────────────────

function ensureDir(filePath: string): void {
  const dir = path.dirname(filePath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

function ensureTables(db: DatabaseSync): void {
  // Blackboard table (mirrors apex/core/blackboard.py _init_table)
  db.exec(`
    CREATE TABLE IF NOT EXISTS blackboard (
        id          TEXT PRIMARY KEY,
        conclusion  TEXT    NOT NULL,
        author      TEXT    NOT NULL DEFAULT '',
        verified    INTEGER NOT NULL DEFAULT 0,
        session_id  TEXT    DEFAULT '',
        created_at  TEXT    DEFAULT '',
        metadata    TEXT    DEFAULT '{}'
    );
  `);
  db.exec(`CREATE INDEX IF NOT EXISTS idx_blackboard_author ON blackboard(author);`);
  db.exec(`CREATE INDEX IF NOT EXISTS idx_blackboard_verified ON blackboard(verified);`);
  db.exec(`CREATE INDEX IF NOT EXISTS idx_blackboard_created ON blackboard(created_at);`);

  // Claims table (mirrors apex/core/claims.py _init_table)
  db.exec(`
    CREATE TABLE IF NOT EXISTS claims (
        task_id       TEXT PRIMARY KEY,
        claimed_by    TEXT    NOT NULL,
        claimed_at    TEXT    DEFAULT '',
        status        TEXT    DEFAULT 'active',
        criteria_json TEXT    DEFAULT '{}',
        findings_json TEXT    DEFAULT '{}',
        verified      INTEGER NOT NULL DEFAULT 0
    );
  `);
  db.exec(`CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(status);`);
  db.exec(`CREATE INDEX IF NOT EXISTS idx_claims_claimed_by ON claims(claimed_by);`);
  db.exec(`CREATE INDEX IF NOT EXISTS idx_claims_claimed_at ON claims(claimed_at);`);
}

// ═══════════════════════════════════════════════════════════════════════════════
// BlackboardAccessor
// ═══════════════════════════════════════════════════════════════════════════════

export interface BlackboardEntry {
  id: string;
  conclusion: string;
  author: string;
  verified: number;
  session_id: string;
  created_at: string;
  metadata: string;
}

export interface BlackboardQueryOpts {
  what?: string;
  filterAuthor?: string;
  verifiedOnly?: boolean;
  sessionId?: string;
  limit?: number;
  offset?: number;
}

export class BlackboardAccessor {
  private _db: DatabaseSync | null = null;
  public readonly dbPath: string;

  constructor(dbPath?: string) {
    this.dbPath = dbPath || DEFAULT_DB_PATH;
  }

  private get db(): DatabaseSync {
    if (this._db) return this._db;
    ensureDir(this.dbPath);
    this._db = new DatabaseSync(this.dbPath);
    this._db.exec("PRAGMA journal_mode = WAL");
    this._db.exec("PRAGMA foreign_keys = ON");
    ensureTables(this._db);
    return this._db;
  }

  query(opts: BlackboardQueryOpts = {}): BlackboardEntry[] {
    const { what, filterAuthor, verifiedOnly, sessionId, limit = 50, offset = 0 } = opts;
    const db = this.db;

    const where: string[] = [];
    const params: unknown[] = [];

    if (filterAuthor) {
      where.push("author = ?");
      params.push(filterAuthor);
    }
    if (verifiedOnly) {
      where.push("verified = 1");
    }
    if (sessionId) {
      where.push("session_id = ?");
      params.push(sessionId);
    }
    if (what) {
      where.push("conclusion LIKE ?");
      params.push(`%${what}%`);
    }

    const clause = where.length > 0 ? "WHERE " + where.join(" AND ") : "";
    const sql = `SELECT * FROM blackboard ${clause} ORDER BY created_at DESC LIMIT ? OFFSET ?`;
    params.push(limit, offset);

    return db.prepare(sql).all(...params) as BlackboardEntry[];
  }

  count(verifiedOnly = false): number {
    const db = this.db;
    const sql = verifiedOnly
      ? "SELECT COUNT(*) as cnt FROM blackboard WHERE verified = 1"
      : "SELECT COUNT(*) as cnt FROM blackboard";
    const row = db.prepare(sql).get() as { cnt: number } | undefined;
    return row?.cnt || 0;
  }

  close(): void {
    if (this._db) {
      this._db.close();
      this._db = null;
    }
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// ClaimsAccessor
// ═══════════════════════════════════════════════════════════════════════════════

export interface ClaimEntry {
  task_id: string;
  claimed_by: string;
  claimed_at: string;
  status: string;
  criteria_json: string;
  findings_json: string;
  verified: number;
}

export interface ClaimsQueryOpts {
  status?: string;
  claimedBy?: string;
  limit?: number;
  offset?: number;
}

export class ClaimsAccessor {
  private _db: DatabaseSync | null = null;
  public readonly dbPath: string;

  constructor(dbPath?: string) {
    this.dbPath = dbPath || DEFAULT_DB_PATH;
  }

  private get db(): DatabaseSync {
    if (this._db) return this._db;
    ensureDir(this.dbPath);
    this._db = new DatabaseSync(this.dbPath);
    this._db.exec("PRAGMA journal_mode = WAL");
    this._db.exec("PRAGMA foreign_keys = ON");
    ensureTables(this._db);
    return this._db;
  }

  query(opts: ClaimsQueryOpts = {}): ClaimEntry[] {
    const { status, claimedBy, limit = 50, offset = 0 } = opts;
    const db = this.db;

    const where: string[] = [];
    const params: unknown[] = [];

    if (status) {
      where.push("status = ?");
      params.push(status);
    }
    if (claimedBy) {
      where.push("claimed_by = ?");
      params.push(claimedBy);
    }

    const clause = where.length > 0 ? "WHERE " + where.join(" AND ") : "";
    const sql = `SELECT * FROM claims ${clause} ORDER BY claimed_at DESC LIMIT ? OFFSET ?`;
    params.push(limit, offset);

    return db.prepare(sql).all(...params) as ClaimEntry[];
  }

  getActive(): ClaimEntry[] {
    return this.query({ status: "active" });
  }

  getClaim(taskId: string): ClaimEntry | undefined {
    const db = this.db;
    return db.prepare("SELECT * FROM claims WHERE task_id = ?").get(taskId) as ClaimEntry | undefined;
  }

  count(status?: string): number {
    const db = this.db;
    const sql = status
      ? "SELECT COUNT(*) as cnt FROM claims WHERE status = ?"
      : "SELECT COUNT(*) as cnt FROM claims";
    const params: unknown[] = status ? [status] : [];
    const row = db.prepare(sql).get(...params) as { cnt: number } | undefined;
    return row?.cnt || 0;
  }

  close(): void {
    if (this._db) {
      this._db.close();
      this._db = null;
    }
  }
}
