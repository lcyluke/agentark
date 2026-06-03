"""
🏛️ 特权操作授权引擎 v3 — 委派 + 作用域边界 + 双重审批 + 审计分身
═══════════════════════════════════════════════════════════════════════════

v3 新增:
  1. 委派体系 — 始祖可将项目级 scope 委派给 PM Agent
  2. 作用域层级 — project:* (PM管) / cross-project:* (双重审批) / system:* (始祖专管)
  3. 双重审批 — 跨项目操作: 始祖预批 → PM终批 → 执行
  4. 资源管理 — model分配 / agent配置 / budget控制 / 审计授权
  5. 审计分身 — audit-guardian 直属始祖，只读审计全局

Scope 命名空间:
  project:{project}:{resource}:{action}    — PM 可批 (被委派范围内)
  project:{project}:model:assign          — 给项目内 agent 分配模型
  project:{project}:config:modify         — 项目级配置修改
  cross-project:{resource}:{action}       — 需要双重审批
  system:{resource}:{action}              — 仅始祖可批
  audit:{action}                          — 审计分身专属

委派模型:
  Origin → apex-pm:     [project:apex:*]           (Apex 项目内全权)
  Origin → yuji-pm:     [project:badminton:*]       (羽球宝项目内全权)
  Origin → content-marketing: [project:shenzhen:*]  (深圳地图内全权)
  Origin → audit-guardian:    [audit:read:*]        (审计分身 — 只读)

双重审批流程 (cross-project):
  1. Agent 请求 → 生成 request_code
  2. 始祖预批 (origin_approved) → 微信确认
  3. PM 终批 (approved) → 生成最终 grant
  4. Agent 执行 → consume
"""

from __future__ import annotations

import hashlib, json, os, sqlite3, time, uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional

AUTH_HOME = Path(os.path.expanduser("~/.hermes/auth"))
AUTH_HOME.mkdir(parents=True, exist_ok=True)
DB_PATH = AUTH_HOME / "grants.db"
AUDIT_LOG = AUTH_HOME / "audit.log"
TZ = timezone(timedelta(hours=8))

ORIGIN_AGENT = "default"  # 始祖 Agent
APPROVED_BY_LUKE = "luke"  # 老卢


# ═══════════════════════════════════════════════════════════════
# Scope 命名空间 v3
# ═══════════════════════════════════════════════════════════════

class ScopeLevel(str, Enum):
    """作用域层级"""
    PROJECT = "project"        # PM 可批 (被委派范围内)
    CROSS_PROJECT = "cross"    # 需双重审批
    SYSTEM = "system"          # 仅始祖
    AUDIT = "audit"            # 审计分身专属


# ── 项目定义 ──────────────────────────────────────────────

PROJECTS = {
    "apex": {
        "name": "Apex Dashboard",
        "emoji": "🦅",
        "pm_agent": "apex-pm",
        "path": "~/Desktop/2026AIAPP/Apex",
    },
    "badminton": {
        "name": "羽球宝AI搭子",
        "emoji": "🏸",
        "pm_agent": "yuji-pm",
        "path": "~/Desktop/2026AIAPP/workspace/badminton-coach-ai",
    },
    "shenzhen": {
        "name": "深圳羽球地图",
        "emoji": "🗺️",
        "pm_agent": "content-marketing",
        "path": "~/Desktop/2026AIAPP/shenzhen-badminton",
    },
}

# ── 委派注册表 (Origin → PM Agent, 项目作用域) ────────────

DELEGATIONS: dict[str, dict] = {
    "apex-pm": {
        "delegated_by": ORIGIN_AGENT,
        "scopes": [
            "project:apex:*",                  # Apex 项目内全权
            "project:apex:model:assign",       # 给项目内 agent 分配模型
            "project:apex:config:modify",      # 项目配置修改
            "project:apex:agent:create",       # 创建项目内 agent
            "project:apex:agent:config",       # 修改项目内 agent 配置
            "autodl:ssh:shutdown",            # AutoDL SSH 关机
            "autodl:api:stop",                # AutoDL API 关机
        ],
        "description": "Apex 平台项目总管 — 可管理 Apex 项目内所有资源和 AutoDL 关停",
    },
    "yuji-pm": {
        "delegated_by": ORIGIN_AGENT,
        "scopes": [
            "project:badminton:*",
            "project:badminton:model:assign",
            "project:badminton:config:modify",
            "project:badminton:agent:create",
            "project:badminton:agent:config",
            "autodl:ssh:shutdown",
            "autodl:api:stop",
        ],
        "description": "羽球宝AI搭子项目总管 — 管理AI教练项目内所有资源",
    },
    "content-marketing": {
        "delegated_by": ORIGIN_AGENT,
        "scopes": [
            "project:shenzhen:*",
            "project:shenzhen:model:assign",
            "project:shenzhen:config:modify",
        ],
        "description": "深圳羽球地图内容推广 — 内容创作和推广配置",
    },
    "audit-guardian": {
        "delegated_by": ORIGIN_AGENT,
        "scopes": [
            "audit:read:*",          # 全局审计只读
            "audit:verify:chain",    # 哈希链验证
            "audit:report:generate", # 审计报告生成
        ],
        "description": "审计守护者 — 始祖分身，只读审计所有授权记录",
    },
}

# ── 完整 Scope 定义 v3 ────────────────────────────────────

READONLY_SCOPES = {
    "autodl:ssh:health",
    "autodl:ssh:status",
    "autodl:ssh:ping",
    "audit:read:*",
    "audit:verify:chain",
}

PRIVILEGED_SCOPES = {
    # ── 项目级资源管理 (PM 可批) ──
    "project:apex:model:assign":      {"risk": "medium", "ttl_min": 60, "desc": "Apex项目内分配模型"},
    "project:apex:config:modify":     {"risk": "high",   "ttl_min": 30, "desc": "修改Apex项目配置"},
    "project:apex:agent:create":      {"risk": "high",   "ttl_min": 30, "desc": "创建Apex项目新agent"},
    "project:apex:agent:config":      {"risk": "medium", "ttl_min": 30, "desc": "修改Apex项目agent配置"},
    "project:badminton:model:assign": {"risk": "medium", "ttl_min": 60, "desc": "羽球宝项目内分配模型"},
    "project:badminton:config:modify":{"risk": "high",   "ttl_min": 30, "desc": "修改羽球宝项目配置"},
    "project:badminton:agent:create": {"risk": "high",   "ttl_min": 30, "desc": "创建羽球宝项目新agent"},
    "project:badminton:agent:config": {"risk": "medium", "ttl_min": 30, "desc": "修改羽球宝项目agent配置"},
    "project:shenzhen:model:assign":  {"risk": "medium", "ttl_min": 60, "desc": "深圳地图项目内分配模型"},
    "project:shenzhen:config:modify": {"risk": "high",   "ttl_min": 30, "desc": "修改深圳地图项目配置"},

    # ── 跨项目资源 (需双重审批) ──
    "cross-project:model:pool:assign":{"risk": "high",   "ttl_min": 30, "desc": "跨项目模型池分配"},
    "cross-project:agent:transfer":   {"risk": "high",   "ttl_min": 20, "desc": "跨项目Agent调动"},
    "cross-project:budget:reallocate":{"risk": "critical","ttl_min": 15, "desc": "跨项目预算重分配"},

    # ── 系统级 (仅始祖) ──
    "system:config:modify":           {"risk": "high",   "ttl_min": 10, "desc": "修改系统配置"},
    "system:cron:modify":             {"risk": "medium", "ttl_min": 10, "desc": "修改 cron 任务"},
    "system:profile:delete":          {"risk": "critical","ttl_min": 5,  "desc": "删除 Profile"},
    "system:delegation:modify":       {"risk": "critical","ttl_min": 5,  "desc": "修改委派关系"},

    # ── 基础设施 (PM可批特定scope) ──
    "autodl:ssh:shutdown":            {"risk": "medium", "ttl_min": 10, "desc": "SSH 安全关机"},
    "autodl:ssh:exec":                {"risk": "high",   "ttl_min": 5,  "desc": "执行远程命令"},
    "autodl:api:start":               {"risk": "medium", "ttl_min": 10, "desc": "API 开机实例"},
    "autodl:api:stop":                {"risk": "medium", "ttl_min": 10, "desc": "API 关机实例"},
    "autodl:api:create":              {"risk": "high",   "ttl_min": 5,  "desc": "创建新实例"},
    "autodl:api:release":             {"risk": "critical","ttl_min": 5,  "desc": "释放实例"},
    "cloud:aws:ec2:terminate":        {"risk": "critical","ttl_min": 5,  "desc": "终止 EC2 实例"},
    "cloud:aws:ec2:start":            {"risk": "medium", "ttl_min": 10, "desc": "启动 EC2 实例"},
    "cloud:aws:ec2:stop":             {"risk": "medium", "ttl_min": 10, "desc": "停止 EC2 实例"},
    "deploy:production:push":         {"risk": "high",   "ttl_min": 10, "desc": "生产环境部署"},
    "hermes:profile:delete":          {"risk": "high",   "ttl_min": 5,  "desc": "删除 Profile"},
    "hermes:config:modify":           {"risk": "high",   "ttl_min": 10, "desc": "修改 Hermes 配置"},

    # ── 审计分身 ──
    "audit:report:generate":          {"risk": "low",   "ttl_min": 120, "desc": "生成审计报告"},
}

RISK_EMOJI = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}
STATUS_ICONS = {
    "pending": "⏳", "approved": "✅", "used": "✔️",
    "expired": "⏰", "revoked": "🚫", "denied": "❌",
    "origin_approved": "🔵",  # 始祖预批，等待PM终批
}


# ═══════════════════════════════════════════════════════════════
# 作用域匹配引擎
# ═══════════════════════════════════════════════════════════════

def classify_scope(scope: str) -> ScopeLevel:
    """判断 scope 属于哪个层级"""
    if scope.startswith("audit:"):
        return ScopeLevel.AUDIT
    if scope.startswith("system:"):
        return ScopeLevel.SYSTEM
    if scope.startswith("cross-project:"):
        return ScopeLevel.CROSS_PROJECT
    if scope.startswith("project:"):
        return ScopeLevel.PROJECT
    # 基础设施 scope (autodl/cloud/deploy/hermes) — 按委派判定
    return ScopeLevel.SYSTEM  # 默认走始祖


def can_approve(agent: str, scope: str) -> tuple[bool, str]:
    """判断一个 Agent 是否可以审批某个 scope

    Returns:
        (can_approve, reason)
    """
    # 始祖 / 老卢: 什么都能批
    if agent in (ORIGIN_AGENT, APPROVED_BY_LUKE, "luke"):
        return True, "始祖/老卢 — 全局权限"

    # 审计分身: 只能批 audit:* scope
    if agent == "audit-guardian":
        if scope.startswith("audit:"):
            return True, "审计分身 — audit scope"
        return False, "审计分身仅限 audit scope"

    # 查委派表
    delegation = DELEGATIONS.get(agent)
    if not delegation:
        return False, f"{agent} 无委派授权"

    allowed = delegation["scopes"]

    # 检查通配匹配
    for pattern in allowed:
        if _scope_matches(pattern, scope):
            return True, f"委派自 {delegation['delegated_by']} — {pattern}"
    return False, f"超出委派范围 ({agent} 仅限 {', '.join(allowed[:3])}...)"


def _scope_matches(pattern: str, scope: str) -> bool:
    """通配 scope 匹配: project:apex:* 匹配 project:apex:model:assign"""
    if pattern == scope:
        return True
    if pattern.endswith(":*"):
        prefix = pattern[:-2]
        return scope.startswith(prefix + ":") or scope == prefix
    return False


def needs_dual_auth(scope: str, requesting_agent: str) -> tuple[bool, Optional[str]]:
    """判断是否需要双重审批

    Returns:
        (needs_dual, reason_or_None)
    """
    level = classify_scope(scope)

    # 跨项目: 必须双重
    if level == ScopeLevel.CROSS_PROJECT:
        return True, "跨项目操作需要始祖预批 + PM终批"

    # 系统级: 仅始祖，不需要双重
    if level == ScopeLevel.SYSTEM:
        return False, None

    # 项目级: PM 被委派 → 不需要双重
    if level == ScopeLevel.PROJECT:
        ok, _ = can_approve(requesting_agent, scope)
        if ok:
            return False, None
        return True, f"{requesting_agent} 未被委派此 scope — 需要始祖双重审批"

    # 审计: 审计分身直批
    if level == ScopeLevel.AUDIT:
        if requesting_agent == "audit-guardian":
            return False, None
        return True, "审计操作仅 audit-guardian 可自行审批"

    return False, None


def get_project_for_scope(scope: str) -> Optional[str]:
    """从 scope 提取项目名"""
    if scope.startswith("project:"):
        parts = scope.split(":")
        if len(parts) >= 2:
            return parts[1]
    return None


def get_project_for_agent(agent: str) -> Optional[str]:
    """根据 agent 推断所属项目"""
    delegation = DELEGATIONS.get(agent)
    if not delegation:
        return None
    for scope in delegation["scopes"]:
        proj = get_project_for_scope(scope)
        if proj:
            return proj
    return None


# ═══════════════════════════════════════════════════════════════
# 数据结构
# ═══════════════════════════════════════════════════════════════

@dataclass
class GrantRecord:
    id: str
    request_code: str
    agent: str
    scope: str
    purpose: str
    risk_level: str
    ttl_min: int
    status: str  # pending | origin_approved | approved | used | expired | revoked | denied
    requested_at: int
    approved_at: Optional[int] = None
    expires_at: Optional[int] = None
    used_at: Optional[int] = None
    revoked_at: Optional[int] = None
    revoked_reason: Optional[str] = None
    approved_by: Optional[str] = None
    origin_approved_by: Optional[str] = None  # v3: 双重审批 — 始祖审批人
    origin_approved_at: Optional[int] = None  # v3: 始祖审批时间
    prev_hash: str = ""
    record_hash: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "request_code": self.request_code,
            "agent": self.agent,
            "scope": self.scope,
            "purpose": self.purpose,
            "risk_level": self.risk_level,
            "ttl_min": self.ttl_min,
            "status": self.status,
            "requested_at": self.requested_at,
            "approved_at": self.approved_at,
            "expires_at": self.expires_at,
            "used_at": self.used_at,
            "revoked_at": self.revoked_at,
            "revoked_reason": self.revoked_reason,
            "approved_by": self.approved_by,
            "origin_approved_by": self.origin_approved_by,
            "origin_approved_at": self.origin_approved_at,
        }

    @property
    def is_expired(self) -> bool:
        if self.expires_at and self.status == "approved":
            return int(time.time()) > self.expires_at
        return False

    @property
    def remaining_minutes(self) -> int:
        if self.expires_at:
            return max(0, (self.expires_at - int(time.time())) // 60)
        return 0

    @property
    def is_dual_auth_ready(self) -> bool:
        """双重审批：始祖已批，PM 待批"""
        return self.status == "origin_approved"


@dataclass
class DelegationRecord:
    """委派记录"""
    id: str
    delegator: str          # 授权人 (始祖)
    delegate: str           # 被委派人 (PM Agent)
    scopes: list[str]       # 委派的 scope 列表
    description: str
    created_at: int
    active: bool = True
    revoked_at: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "delegator": self.delegator,
            "delegate": self.delegate,
            "scopes": self.scopes,
            "description": self.description,
            "active": self.active,
            "created_at": self.created_at,
            "revoked_at": self.revoked_at,
        }


@dataclass
class AuthCheckResult:
    authorized: bool
    message: str
    grant_id: Optional[str] = None
    request_code: Optional[str] = None
    remaining_minutes: int = 0
    scope: str = ""
    agent: str = ""


@dataclass
class AuditEntry:
    id: int
    timestamp: int
    action: str
    grant_id: str
    request_code: str
    agent: str
    scope: str
    detail: str
    chain_hash: str


# ═══════════════════════════════════════════════════════════════
# 哈希链
# ═══════════════════════════════════════════════════════════════

def hash_record(prev_hash: str, data: str) -> str:
    raw = f"{prev_hash}|{data}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ═══════════════════════════════════════════════════════════════
# 审计
# ═══════════════════════════════════════════════════════════════

def write_audit(action: str, grant_id: str = "", request_code: str = "",
                agent: str = "", scope: str = "", detail: str = "",
                chain_hash: str = ""):
    ts = int(time.time())
    timestamp_str = datetime.fromtimestamp(ts, TZ).strftime("%Y-%m-%d %H:%M:%S")
    log_entry = (f"[{timestamp_str}] {action:12s} | {request_code:8s} | "
                 f"{agent:16s} | {scope:28s} | {detail}")
    with open(AUDIT_LOG, "a") as f:
        f.write(log_entry + "\n")


# ═══════════════════════════════════════════════════════════════
# 数据库层 (v3 — 新增 delegation 表)
# ═══════════════════════════════════════════════════════════════

class AuthorizationDB:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_tables()
        self._sync_delegations()

    def _init_tables(self):
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS grants (
                    id TEXT PRIMARY KEY,
                    request_code TEXT UNIQUE NOT NULL,
                    agent TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    risk_level TEXT NOT NULL DEFAULT 'medium',
                    ttl_min INTEGER NOT NULL DEFAULT 10,
                    status TEXT NOT NULL DEFAULT 'pending',
                    requested_at INTEGER NOT NULL,
                    approved_at INTEGER,
                    expires_at INTEGER,
                    used_at INTEGER,
                    revoked_at INTEGER,
                    revoked_reason TEXT,
                    approved_by TEXT,
                    origin_approved_by TEXT,
                    origin_approved_at INTEGER,
                    prev_hash TEXT NOT NULL,
                    record_hash TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            # v3: 委派表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS delegations (
                    id TEXT PRIMARY KEY,
                    delegator TEXT NOT NULL,
                    delegate TEXT NOT NULL,
                    scopes TEXT NOT NULL DEFAULT '[]',
                    description TEXT DEFAULT '',
                    active INTEGER DEFAULT 1,
                    created_at INTEGER NOT NULL,
                    revoked_at INTEGER
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    grant_id TEXT,
                    request_code TEXT,
                    agent TEXT,
                    scope TEXT,
                    detail TEXT,
                    chain_hash TEXT NOT NULL
                )
            """)
            # v3: 迁移 — 加 origin_approved 相关列
            try:
                conn.execute("ALTER TABLE grants ADD COLUMN origin_approved_by TEXT")
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute("ALTER TABLE grants ADD COLUMN origin_approved_at INTEGER")
            except sqlite3.OperationalError:
                pass
            conn.commit()

    def _sync_delegations(self):
        """将代码中定义的委派关系同步到 DB"""
        with sqlite3.connect(str(self.db_path)) as conn:
            existing = {
                row[0]: row
                for row in conn.execute(
                    "SELECT delegate, id, scopes FROM delegations WHERE active=1"
                ).fetchall()
            }
            now = int(time.time())
            for delegate, cfg in DELEGATIONS.items():
                scopes_json = json.dumps(cfg["scopes"])
                if delegate in existing:
                    # 更新 scope 如果变了
                    if existing[delegate][2] != scopes_json:
                        conn.execute(
                            "UPDATE delegations SET scopes=? WHERE delegate=? AND active=1",
                            (scopes_json, delegate),
                        )
                else:
                    dlgt_id = uuid.uuid4().hex[:12]
                    conn.execute(
                        """INSERT INTO delegations (id, delegator, delegate, scopes, description, active, created_at)
                           VALUES (?, ?, ?, ?, ?, 1, ?)""",
                        (dlgt_id, cfg["delegated_by"], delegate, scopes_json,
                         cfg["description"], now),
                    )
            conn.commit()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def get_prev_hash(self, conn: sqlite3.Connection) -> str:
        row = conn.execute(
            "SELECT record_hash FROM grants ORDER BY requested_at DESC LIMIT 1"
        ).fetchone()
        return row["record_hash"] if row else "0" * 16

    def insert_grant(self, grant: GrantRecord):
        with self.get_connection() as conn:
            conn.execute(
                """INSERT INTO grants
                   (id, request_code, agent, scope, purpose, risk_level, ttl_min,
                    status, requested_at, prev_hash, record_hash,
                    origin_approved_by, origin_approved_at, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (grant.id, grant.request_code, grant.agent, grant.scope,
                 grant.purpose, grant.risk_level, grant.ttl_min, grant.status,
                 grant.requested_at, grant.prev_hash, grant.record_hash,
                 grant.origin_approved_by, grant.origin_approved_at,
                 json.dumps(grant.metadata)),
            )
            conn.commit()

    def get_grant(self, request_code: str = "", grant_id: str = "") -> Optional[GrantRecord]:
        with self.get_connection() as conn:
            if request_code:
                row = conn.execute(
                    "SELECT * FROM grants WHERE request_code = ?", (request_code,)
                ).fetchone()
            elif grant_id:
                row = conn.execute(
                    "SELECT * FROM grants WHERE id = ?", (grant_id,)
                ).fetchone()
            else:
                return None
            if not row:
                return None
            return self._row_to_grant(row)

    def _row_to_grant(self, row) -> GrantRecord:
        return GrantRecord(
            id=row["id"], request_code=row["request_code"],
            agent=row["agent"], scope=row["scope"], purpose=row["purpose"],
            risk_level=row["risk_level"], ttl_min=row["ttl_min"],
            status=row["status"], requested_at=row["requested_at"],
            approved_at=row["approved_at"], expires_at=row["expires_at"],
            used_at=row["used_at"], revoked_at=row["revoked_at"],
            revoked_reason=row["revoked_reason"], approved_by=row["approved_by"],
            origin_approved_by=row["origin_approved_by"] if "origin_approved_by" in row.keys() else None,
            origin_approved_at=row["origin_approved_at"] if "origin_approved_at" in row.keys() else None,
            prev_hash=row["prev_hash"], record_hash=row["record_hash"],
            metadata=json.loads(row["metadata"] or "{}"),
        )

    def find_valid_grant(self, agent: str, scope: str) -> Optional[GrantRecord]:
        now = int(time.time())
        with self.get_connection() as conn:
            row = conn.execute(
                """SELECT * FROM grants
                   WHERE agent = ? AND scope = ? AND status = 'approved'
                   AND expires_at > ?
                   ORDER BY approved_at DESC LIMIT 1""",
                (agent, scope, now),
            ).fetchone()
            return self._row_to_grant(row) if row else None

    def update_status(self, grant_id: str, status: str, **kwargs):
        with self.get_connection() as conn:
            fields = ["status = ?"]
            values = [status]
            for key, val in kwargs.items():
                if val is not None:
                    fields.append(f"{key} = ?")
                    values.append(val)
            values.append(grant_id)
            conn.execute(
                f"UPDATE grants SET {', '.join(fields)} WHERE id = ?", values
            )
            conn.commit()

    def append_record_hash(self, grant_id: str, suffix: str, new_hash: str):
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE grants SET record_hash = record_hash || ? || ? WHERE id = ?",
                (suffix, new_hash, grant_id),
            )
            conn.commit()

    def list_grants(self, agent: str = "", scope: str = "",
                    status: str = "", limit: int = 50) -> list[GrantRecord]:
        query = "SELECT * FROM grants WHERE 1=1"
        params: list = []
        if agent:
            query += " AND agent = ?"
            params.append(agent)
        if scope:
            query += " AND scope LIKE ?"
            params.append(f"%{scope}%")
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY requested_at DESC LIMIT ?"
        params.append(limit)
        results = []
        with self.get_connection() as conn:
            for row in conn.execute(query, params).fetchall():
                results.append(self._row_to_grant(row))
        return results

    def list_delegations(self, delegator: str = "", delegate: str = "") -> list[DelegationRecord]:
        with self.get_connection() as conn:
            query = "SELECT * FROM delegations WHERE 1=1"
            params = []
            if delegator:
                query += " AND delegator = ?"
                params.append(delegator)
            if delegate:
                query += " AND delegate = ?"
                params.append(delegate)
            query += " ORDER BY created_at DESC"
            results = []
            for row in conn.execute(query, params).fetchall():
                results.append(DelegationRecord(
                    id=row["id"], delegator=row["delegator"],
                    delegate=row["delegate"],
                    scopes=json.loads(row["scopes"]),
                    description=row["description"],
                    created_at=row["created_at"],
                    active=bool(row["active"]),
                    revoked_at=row["revoked_at"],
                ))
            return results

    def get_audit_logs(self, days: int = 7, limit: int = 200) -> list[AuditEntry]:
        cutoff = int(time.time()) - days * 86400
        results = []
        with self.get_connection() as conn:
            for row in conn.execute(
                "SELECT * FROM audit_log WHERE timestamp > ? ORDER BY timestamp DESC LIMIT ?",
                (cutoff, limit),
            ).fetchall():
                results.append(AuditEntry(
                    id=row["id"], timestamp=row["timestamp"],
                    action=row["action"], grant_id=row["grant_id"] or "",
                    request_code=row["request_code"] or "",
                    agent=row["agent"] or "", scope=row["scope"] or "",
                    detail=row["detail"] or "", chain_hash=row["chain_hash"],
                ))
        return results

    def verify_chain(self) -> tuple[bool, int, list[str]]:
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT id, request_code, prev_hash, record_hash FROM grants ORDER BY requested_at ASC"
            ).fetchall()
        if not rows:
            return True, 0, []
        prev_hash = "0" * 16
        breaks = []
        for r in rows:
            if r["prev_hash"] != prev_hash:
                breaks.append(f"断裂 @ {r['id']} code={r['request_code']} "
                             f"期望={prev_hash} 实际={r['prev_hash']}")
            prev_hash = r["record_hash"]
        return len(breaks) == 0, len(rows), breaks

    def stats(self) -> dict:
        now = int(time.time())
        with self.get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) FROM grants").fetchone()[0]
            pending = conn.execute("SELECT COUNT(*) FROM grants WHERE status='pending' OR status='origin_approved'").fetchone()[0]
            active = conn.execute("SELECT COUNT(*) FROM grants WHERE status='approved' AND expires_at > ?", (now,)).fetchone()[0]
            used = conn.execute("SELECT COUNT(*) FROM grants WHERE status='used'").fetchone()[0]
            scope_counts = {}
            for row in conn.execute("SELECT scope, COUNT(*) as cnt FROM grants GROUP BY scope ORDER BY cnt DESC").fetchall():
                scope_counts[row["scope"]] = row["cnt"]
            delegations = conn.execute("SELECT COUNT(*) FROM delegations WHERE active=1").fetchone()[0]
        return {
            "total": total, "pending": pending, "active": active, "used": used,
            "by_scope": scope_counts, "active_delegations": delegations,
        }


# ═══════════════════════════════════════════════════════════════
# 核心引擎 v3
# ═══════════════════════════════════════════════════════════════

class AuthorizationEngine:
    """特权操作授权引擎 v3 — 委派 + 双重审批 + 审计分身"""

    def __init__(self):
        self.db = AuthorizationDB()

    # ── 委派管理 ────────────────────────────────────────────

    def list_delegations(self, delegator: str = "", delegate: str = "") -> list[dict]:
        return [d.to_dict() for d in self.db.list_delegations(delegator, delegate)]

    def modify_delegation(self, delegator: str, delegate: str,
                          scopes: list[str], description: str = "") -> dict:
        """修改委派关系 (仅始祖)"""
        if delegator != ORIGIN_AGENT:
            return {"ok": False, "error": "仅始祖可修改委派关系"}

        now = int(time.time())
        with self.db.get_connection() as conn:
            # 撤销旧委派
            conn.execute(
                "UPDATE delegations SET active=0, revoked_at=? WHERE delegate=? AND active=1",
                (now, delegate),
            )
            # 创建新委派
            dlgt_id = uuid.uuid4().hex[:12]
            conn.execute(
                """INSERT INTO delegations (id, delegator, delegate, scopes, description, active, created_at)
                   VALUES (?, ?, ?, ?, ?, 1, ?)""",
                (dlgt_id, delegator, delegate, json.dumps(scopes), description, now),
            )
            conn.commit()

        write_audit("DELEGATION_MODIFY", agent=delegator, scope="system:delegation:modify",
                    detail=f"delegated to {delegate}: {scopes}")
        return {"ok": True, "delegate": delegate, "scopes": scopes}

    def revoke_delegation(self, delegator: str, delegate: str) -> dict:
        """吊销委派"""
        if delegator != ORIGIN_AGENT:
            return {"ok": False, "error": "仅始祖可吊销委派"}
        now = int(time.time())
        with self.db.get_connection() as conn:
            conn.execute(
                "UPDATE delegations SET active=0, revoked_at=? WHERE delegate=? AND active=1",
                (now, delegate),
            )
            conn.commit()
        write_audit("DELEGATION_REVOKE", agent=delegator, scope="system:delegation:modify",
                    detail=f"revoked {delegate}")
        return {"ok": True, "delegate": delegate}

    # ── 授权请求 ────────────────────────────────────────────

    def request(self, agent: str, scope: str, purpose: str,
                metadata: Optional[dict] = None, ttl_min: Optional[int] = None) -> dict:
        """请求授权 — v3 支持双重审批判断"""
        if scope in READONLY_SCOPES:
            return {"ok": True, "bypass": True, "message": f"{scope} 是只读操作，无需授权"}

        config = PRIVILEGED_SCOPES.get(scope, {"risk": "unknown", "ttl_min": 5, "desc": scope})
        risk = config["risk"]
        ttl = ttl_min or config["ttl_min"]

        # 检查是否需要双重审批
        dual_needed, dual_reason = needs_dual_auth(scope, agent)

        # 检查是否有权审批
        can_app, reason = can_approve(agent, scope)
        if not can_app:
            # 如果是跨项目或超范围 → 自动请求双重审批
            if dual_needed:
                pass  # 继续，走双重流程
            else:
                return {"ok": False, "error": f"无权限: {reason}"}

        grant_id = uuid.uuid4().hex[:12]
        request_code = str(int(time.time() * 1000) % 1000000).zfill(6)
        now = int(time.time())

        prev_hash = "0" * 16
        with self.db.get_connection() as conn:
            prev_hash = self.db.get_prev_hash(conn)

        hash_data = f"{grant_id}|{request_code}|{agent}|{scope}|{purpose}|{now}"
        record_hash = hash_record(prev_hash, hash_data)

        grant = GrantRecord(
            id=grant_id, request_code=request_code, agent=agent,
            scope=scope, purpose=purpose, risk_level=risk,
            ttl_min=ttl, status="pending", requested_at=now,
            prev_hash=prev_hash, record_hash=record_hash,
            metadata=metadata or {},
        )
        self.db.insert_grant(grant)

        write_audit("REQUEST", grant_id, request_code, agent, scope, purpose, record_hash)

        result = {
            "ok": True, "grant_id": grant_id, "request_code": request_code,
            "agent": agent, "scope": scope, "purpose": purpose,
            "risk": risk, "risk_emoji": RISK_EMOJI.get(risk, "❓"),
            "ttl_min": ttl, "description": config.get("desc", ""),
            "dual_auth_required": dual_needed,
        }

        if dual_needed:
            result["dual_auth_reason"] = dual_reason
            result["dual_auth_flow"] = "始祖预批 → PM终批 → Agent执行"

        return result

    # ── 始祖预批 (双重审批第一步) ────────────────────────────

    def origin_pre_approve(self, request_code: str) -> dict:
        """始祖预批 — 双重审批的第一步"""
        grant = self.db.get_grant(request_code=request_code)
        if not grant:
            return {"ok": False, "error": f"授权码 {request_code} 不存在"}

        if grant.status != "pending":
            return {"ok": False, "error": f"授权 {request_code} 状态为 {grant.status}"}

        dual_needed, _ = needs_dual_auth(grant.scope, grant.agent)
        now = int(time.time())

        hash_data = f"ORIGIN_APPROVE|{grant.id}|{request_code}|{now}"
        record_hash = hash_record(grant.record_hash, hash_data)

        self.db.update_status(grant.id, "origin_approved",
                              origin_approved_by=ORIGIN_AGENT,
                              origin_approved_at=now)
        self.db.append_record_hash(grant.id, "|ORIGIN_APPROVE|", record_hash)

        write_audit("ORIGIN_APPROVE", grant.id, request_code, grant.agent,
                    grant.scope, f"pre-approved by {ORIGIN_AGENT}", record_hash)

        result = {
            "ok": True, "grant_id": grant.id, "request_code": request_code,
            "agent": grant.agent, "scope": grant.scope,
            "dual_auth_required": dual_needed,
        }

        if dual_needed:
            level = classify_scope(grant.scope)
            if level == ScopeLevel.CROSS_PROJECT:
                result["next_step"] = "等待始祖终批 (跨项目操作)"
                result["final_approver"] = ORIGIN_AGENT
            else:
                # 超范围项目操作 — 找所属 PM
                project = get_project_for_scope(grant.scope)
                if project and project in PROJECTS:
                    pm = PROJECTS[project]["pm_agent"]
                    result["next_step"] = f"等待 {pm} 终批"
                    result["pm_agent"] = pm
                else:
                    result["next_step"] = "等待 PM 终批"
        else:
            # 非双重审批 → 始祖直接批了
            expires_at = now + grant.ttl_min * 60
            self.db.update_status(grant.id, "approved",
                                  approved_at=now, expires_at=expires_at,
                                  approved_by=ORIGIN_AGENT)
            result["status"] = "approved"
            result["expires_at"] = expires_at

        return result

    # ── PM 终批 (双重审批第二步) ─────────────────────────────

    def approve(self, request_code: str, approved_by: str = "") -> dict:
        """审批授权 — 支持 PM 终批和直接审批"""
        grant = self.db.get_grant(request_code=request_code)
        if not grant:
            return {"ok": False, "error": f"授权码 {request_code} 不存在"}

        approver = approved_by or APPROVED_BY_LUKE

        if grant.status == "origin_approved":
            # 双重审批第二步: 终批
            # 跨项目 scope → 仅始祖/老卢可终批
            # 项目 scope（超范围）→ PM 终批
            level = classify_scope(grant.scope)

            if level == ScopeLevel.CROSS_PROJECT:
                if approver not in (ORIGIN_AGENT, APPROVED_BY_LUKE, "luke"):
                    return {"ok": False,
                            "error": f"跨项目授权需始祖终批。{approver} 无权终批跨项目操作"}

            elif level == ScopeLevel.PROJECT:
                can_app, reason = can_approve(approver, grant.scope)
                if not can_app:
                    return {"ok": False, "error": f"{approver} 无权审批: {reason}"}
            else:
                if approver not in (ORIGIN_AGENT, APPROVED_BY_LUKE, "luke"):
                    return {"ok": False, "error": f"{grant.scope} 需始祖终批"}

            now = int(time.time())
            expires_at = now + grant.ttl_min * 60

            hash_data = f"FINAL_APPROVE|{grant.id}|{request_code}|{now}|{expires_at}|{approver}"
            record_hash = hash_record(grant.record_hash, hash_data)

            self.db.update_status(grant.id, "approved",
                                  approved_at=now, expires_at=expires_at,
                                  approved_by=approver)
            self.db.append_record_hash(grant.id, "|FINAL_APPROVE|", record_hash)

            write_audit("FINAL_APPROVE", grant.id, request_code, grant.agent,
                        grant.scope, f"final-approved by {approver} (origin pre-approved)", record_hash)

            return {
                "ok": True, "grant_id": grant.id, "request_code": request_code,
                "agent": grant.agent, "scope": grant.scope,
                "expires_at": expires_at, "ttl_min": grant.ttl_min,
                "dual_auth_complete": True,
                "approved_by": f"{ORIGIN_AGENT} → {approver}",
            }

        elif grant.status == "pending":
            # 单步审批: 始祖或老卢直接批
            if approver not in (ORIGIN_AGENT, APPROVED_BY_LUKE):
                # 非始祖 → 检查委派
                can_app, reason = can_approve(approver, grant.scope)
                if not can_app:
                    # 检查是否需要双重
                    dual_needed, _ = needs_dual_auth(grant.scope, grant.agent)
                    if dual_needed:
                        return {"ok": False, "error": f"此操作需要双重审批: 先由始祖预批。{reason}"}
                    return {"ok": False, "error": f"无权限: {reason}"}

            now = int(time.time())
            expires_at = now + grant.ttl_min * 60

            hash_data = f"APPROVE|{grant.id}|{request_code}|{now}|{expires_at}|{approver}"
            record_hash = hash_record(grant.record_hash, hash_data)

            self.db.update_status(grant.id, "approved",
                                  approved_at=now, expires_at=expires_at,
                                  approved_by=approver)
            self.db.append_record_hash(grant.id, "|APPROVE|", record_hash)

            write_audit("APPROVE", grant.id, request_code, grant.agent,
                        grant.scope, f"approved by {approver}", record_hash)

            return {
                "ok": True, "grant_id": grant.id, "request_code": request_code,
                "agent": grant.agent, "scope": grant.scope,
                "expires_at": expires_at, "ttl_min": grant.ttl_min,
                "dual_auth_complete": False,
            }

        else:
            return {"ok": False, "error": f"授权 {request_code} 状态为 {grant.status}，不可审批"}

    # ── 基础操作 (拒绝/检查/使用/吊销) ────────────────────────

    def deny(self, request_code: str) -> dict:
        grant = self.db.get_grant(request_code=request_code)
        if not grant:
            return {"ok": False, "error": f"授权码 {request_code} 不存在"}
        now = int(time.time())
        self.db.update_status(grant.id, "denied", revoked_at=now)
        write_audit("DENY", grant.id, request_code, grant.agent,
                    grant.scope, "denied by user")
        return {"ok": True, "grant_id": grant.id, "request_code": request_code}

    def check(self, agent: str, scope: str) -> AuthCheckResult:
        if scope in READONLY_SCOPES:
            return AuthCheckResult(authorized=True, message="readonly — 免授权",
                                   scope=scope, agent=agent)
        grant = self.db.find_valid_grant(agent, scope)
        if grant:
            remaining = grant.remaining_minutes
            return AuthCheckResult(
                authorized=True,
                message=f"已授权 #{grant.request_code} · 剩余 {remaining} 分钟",
                grant_id=grant.id, request_code=grant.request_code,
                remaining_minutes=remaining, scope=scope, agent=agent,
            )
        return AuthCheckResult(authorized=False, message="未授权", scope=scope, agent=agent)

    def consume(self, grant_id: str) -> dict:
        grant = self.db.get_grant(grant_id=grant_id)
        if not grant:
            return {"ok": False, "error": f"授权 {grant_id} 不存在"}
        if grant.status != "approved":
            return {"ok": False, "error": f"授权 {grant_id} 状态为 {grant.status}"}
        now = int(time.time())
        self.db.update_status(grant.id, "used", used_at=now)
        write_audit("CONSUME", grant.id, "", grant.agent, grant.scope, "used")
        return {"ok": True, "grant_id": grant_id, "agent": grant.agent, "scope": grant.scope}

    def revoke(self, grant_id_or_code: str, reason: str = "") -> dict:
        grant = (self.db.get_grant(grant_id=grant_id_or_code) or
                 self.db.get_grant(request_code=grant_id_or_code))
        if not grant:
            return {"ok": False, "error": f"授权 {grant_id_or_code} 不存在"}
        now = int(time.time())
        self.db.update_status(grant.id, "revoked", revoked_at=now, revoked_reason=reason)
        write_audit("REVOKE", grant.id, "", grant.agent, grant.scope, reason or "revoked")
        return {"ok": True, "grant_id": grant.id, "grant_id_or_code": grant_id_or_code, "reason": reason}

    # ── 查询 ─────────────────────────────────────────────────

    def list_grants(self, agent: str = "", scope: str = "",
                    status: str = "", limit: int = 50) -> list[dict]:
        return [g.to_dict() for g in self.db.list_grants(agent, scope, status, limit)]

    def get_audit(self, days: int = 7, limit: int = 200) -> list[dict]:
        logs = self.db.get_audit_logs(days=days, limit=limit)
        return [{
            "id": l.id, "timestamp": l.timestamp,
            "timestamp_str": datetime.fromtimestamp(l.timestamp, TZ).strftime("%Y-%m-%d %H:%M:%S"),
            "action": l.action, "grant_id": l.grant_id,
            "request_code": l.request_code, "agent": l.agent,
            "scope": l.scope, "detail": l.detail, "chain_hash": l.chain_hash,
        } for l in logs]

    def verify(self) -> dict:
        ok, total, breaks = self.db.verify_chain()
        return {"valid": ok, "total_records": total, "breaks": breaks}

    def stats(self) -> dict:
        return self.db.stats()

    def get_scopes(self) -> dict:
        return {
            "readonly": sorted(list(READONLY_SCOPES)),
            "privileged": {
                scope: {"risk": cfg["risk"], "ttl_min": cfg["ttl_min"],
                        "desc": cfg["desc"], "emoji": RISK_EMOJI.get(cfg["risk"], "❓")}
                for scope, cfg in PRIVILEGED_SCOPES.items()
            },
        }

    # ── v3 专有 ──────────────────────────────────────────────

    def get_delegation_matrix(self) -> dict:
        """委派矩阵 — 谁可以批什么"""
        matrix = {}
        for delegate, cfg in DELEGATIONS.items():
            matrix[delegate] = {
                "delegated_by": cfg["delegated_by"],
                "scopes": cfg["scopes"],
                "description": cfg["description"],
                "project": get_project_for_agent(delegate),
            }
        return matrix

    def check_delegation_scope(self, delegate: str, scope: str) -> dict:
        """检查某个 scope 是否在委派范围内"""
        can_app, reason = can_approve(delegate, scope)
        dual_needed, dual_reason = needs_dual_auth(scope, delegate)
        return {
            "delegate": delegate,
            "scope": scope,
            "can_approve": can_app,
            "reason": reason,
            "dual_auth_required": dual_needed,
            "dual_auth_reason": dual_reason,
        }


# ═══════════════════════════════════════════════════════════════
# 模块级便捷 API
# ═══════════════════════════════════════════════════════════════

_engine: Optional[AuthorizationEngine] = None

def get_engine() -> AuthorizationEngine:
    global _engine
    if _engine is None:
        _engine = AuthorizationEngine()
    return _engine
