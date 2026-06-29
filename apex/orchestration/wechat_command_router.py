"""
微信并行多Agent命令路由器 v1
═══════════════════════════════════════════════

支持在同一个微信对话中通过前缀命令并行调度多个项目的Agent。

命令格式:
  P1: <消息>        → 路由到P1(羽球宝)的PM Agent
  P2: <消息>        → 路由到P2(Apex)的PM Agent  
  P3: <消息>        → 路由到P3(深圳地图)的PM Agent
  P4: <消息>        → 路由到P4(FinOps)的PM Agent

角色子命令:
  P1:req <需求>     → P1 需求分析 Agent (architect)
  P1:dev <任务>     → P1 开发 Agent (architect/frontend-dev)
  P1:qa <测试>      → P1 测试 Agent (frontend-dev)
  P1:dep <部署>     → P1 部署 Agent (ops-engineer)
  P1:sec <安全>     → P1 安全 Agent (security-compliance)
  
  P2:dev <任务>     → P2 开发 Agent (apex-pm)
  P3:content <内容> → P3 内容 Agent (content-marketing)
  P4:cost <成本>    → P4 成本分析 Agent (finops-pm)

签退: 当Agent完成回复后，自动附加签名
  "PM1-agent：收到回复，消息…"

回退: 不加前缀的消息 → 使用关键词路由器(message_router)自动识别

集成:
  - Apex Dashboard: 日志记录到 kanban.db
  - Hermes Profile: 设置会话上下文
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ── 项目定义 (P1-P4) ─────────────────────────────────────

@dataclass
class ProjectDef:
    code: str           # P1, P2, P3, P4
    name: str           # 项目中文名
    emoji: str
    router_key: str     # message_router.py 中的 project key
    pm_profile: str     # PM Agent profile
    pm_name: str        # PM Agent 签名名
    # 角色映射: 子命令 → (profile, role_name, emoji)
    roles: dict[str, tuple[str, str, str]] = field(default_factory=dict)

PROJECTS: dict[str, ProjectDef] = {
    "P1": ProjectDef(
        code="P1",
        name="羽球宝AI搭子",
        emoji="🏸",
        router_key="badminton-coach-ai",
        pm_profile="badminton-pm",
        pm_name="PM1-agent",
        roles={
            "req":  ("architect",          "需求分析师", "📋"),
            "dev":  ("architect",          "开发工程师", "💻"),
            "qa":   ("frontend-dev",       "测试工程师", "🧪"),
            "dep":  ("ops-engineer",       "部署工程师", "🚀"),
            "sec":  ("security-compliance","安全审计",   "🔒"),
            "ai":   ("ai-algorithm",       "AI算法专家", "🧠"),
            "vis":  ("ai-vision",          "视觉专家",   "👁️"),
            "ui":   ("frontend-dev",       "前端开发",   "🎨"),
            "pm":   ("badminton-pm",       "项目经理",   "🎯"),
            "content": ("content-marketing", "内容运营", "✍️"),
        },
    ),
    "P2": ProjectDef(
        code="P2",
        name="Apex Dashboard",
        emoji="🦅",
        router_key="apex",
        pm_profile="apex-pm",
        pm_name="PM2-agent",
        roles={
            "dev":  ("apex-pm",           "平台开发",   "💻"),
            "ops":  ("ops-engineer",      "运维部署",   "🔧"),
            "sec":  ("security-compliance","安全合规",   "🔒"),
            "pm":   ("apex-pm",           "平台总管",   "🦅"),
        },
    ),
    "P3": ProjectDef(
        code="P3",
        name="深圳羽球地图",
        emoji="🗺️",
        router_key="shenzhen-badminton",
        pm_profile="content-marketing",
        pm_name="PM3-agent",
        roles={
            "content": ("content-marketing", "内容运营", "✍️"),
            "data":    ("content-marketing", "数据分析", "📊"),
            "pm":      ("content-marketing", "项目经理", "🎯"),
        },
    ),
    "P4": ProjectDef(
        code="P4",
        name="FinOps AI",
        emoji="💰",
        router_key="finopsai",
        pm_profile="finops-pm",
        pm_name="PM4-agent",
        roles={
            "cost":   ("finops-pm",        "成本分析",   "💰"),
            "dev":    ("finops-architect", "架构开发",   "💻"),
            "ops":    ("finops-devops",    "运维部署",   "🔧"),
            "pm":     ("finops-pm",        "项目经理",   "📊"),
        },
    ),
}

# ── 命令解析正则 ─────────────────────────────────────────

# 三步解析:
#   Step 1: 提取项目代码 P1-P4 和剩余部分
#   Step 2: 从剩余部分提取可选的角色子命令
#   Step 3: 剩余为消息体

PROJECT_PREFIX = re.compile(r'^(P[1-4])\s*[:：]\s*(.*)', re.IGNORECASE)
SHORT_PATTERN = re.compile(r'^(P[1-4])$', re.IGNORECASE)


def _parse_command(msg: str) -> tuple[str, str, str]:
    """解析命令字符串，返回 (project_code, role_code, message_body)
    
    支持的格式:
      P1:消息           → ("P1", "pm", "消息")
      P1:dev 消息       → ("P1", "dev", "消息")
      P1:dev:消息       → ("P1", "dev", "消息")
      P2:ops 部署上线   → ("P2", "ops", "部署上线")
    """
    msg = msg.strip()
    
    # 先提取 P1: 前缀
    m = PROJECT_PREFIX.match(msg)
    if not m:
        return ("", "", msg)
    
    code = m.group(1).upper()
    rest = m.group(2).strip()
    
    if not rest:
        return (code, "pm", "")
    
    # 检查 rest 是否以 角色:消息 或 角色 消息 开头
    # 已知的角色代码
    known_roles = {"req", "dev", "qa", "dep", "sec", "ai", "vis", "ui", 
                   "pm", "content", "ops", "data", "cost"}
    
    # 尝试匹配 "role:消息" 或 "role 消息"
    role_match = re.match(r'^(\w+)\s*[:：]\s*(.*)', rest)
    if role_match:
        potential_role = role_match.group(1).lower()
        if potential_role in known_roles:
            return (code, potential_role, role_match.group(2).strip())
    
    # 尝试匹配 "role 消息" (空格分隔)
    space_match = re.match(r'^(\w+)\s+(.+)', rest)
    if space_match:
        potential_role = space_match.group(1).lower()
        if potential_role in known_roles:
            return (code, potential_role, space_match.group(2).strip())
    
    # 只有角色没有消息
    if rest.lower() in known_roles:
        return (code, rest.lower(), "")
    
    # 没有匹配到已知角色 → rest 就是消息体，默认PM
    return (code, "pm", rest)


@dataclass
class CommandResult:
    """命令解析结果"""
    parsed: bool                    # 是否成功解析为命令
    project_code: str = ""          # P1/P2/P3/P4
    project: Optional[ProjectDef] = None
    role_code: str = ""             # req/dev/qa/dep/sec/pm
    role_profile: str = ""          # Hermes profile name
    role_name: str = ""             # 角色中文名
    role_emoji: str = ""
    agent_signature: str = ""       # "PM1-agent" 或 "PM1-agent·开发工程师"
    message: str = ""               # 去前缀后的消息体
    is_signoff: bool = False        # 是否签退命令(仅P1无消息)
    raw: str = ""                   # 原始消息


class WeChatCommandRouter:
    """微信并行多Agent命令路由器"""

    def __init__(self, dashboard_log_path: str = ""):
        self._log_path = Path(dashboard_log_path) if dashboard_log_path else None
        # 活跃会话: {project_code: {role_code: last_context}}
        self._sessions: dict[str, dict] = {}

    # ── 命令解析 ─────────────────────────────────────────

    def parse(self, message: str) -> CommandResult:
        """解析微信消息，识别是否为显式命令

        Returns:
            CommandResult with parsed=True if P1:/P2: prefix detected
        """
        msg = message.strip()

        # 快捷: 仅 P1 / P2 (签退确认)
        short_match = SHORT_PATTERN.match(msg)
        if short_match:
            code = short_match.group(1).upper()
            proj = PROJECTS.get(code)
            if proj:
                return CommandResult(
                    parsed=True,
                    project_code=code,
                    project=proj,
                    role_code="pm",
                    role_profile=proj.pm_profile,
                    role_name="项目经理",
                    role_emoji="🎯",
                    agent_signature=proj.pm_name,
                    message="",
                    is_signoff=True,
                    raw=msg,
                )

        # 完整命令: P1:消息 或 P1:dev 消息 或 P1:dev:消息
        code, role_code, body = _parse_command(msg)
        if not code:
            return CommandResult(parsed=False, raw=msg)

        proj = PROJECTS.get(code)
        if not proj:
            return CommandResult(parsed=False, raw=msg)

        # 解析角色
        role_info = proj.roles.get(role_code)
        if role_info:
            profile, role_name, role_emoji = role_info
        else:
            # 未知子命令 → 回退到PM
            profile = proj.pm_profile
            role_name = "项目经理"
            role_emoji = "🎯"
            role_code = "pm"

        # 构建签名
        if role_code == "pm":
            signature = proj.pm_name
        else:
            signature = f"{proj.pm_name}·{role_name}"

        # 更新活跃会话
        self._set_session(code, role_code)

        return CommandResult(
            parsed=True,
            project_code=code,
            project=proj,
            role_code=role_code,
            role_profile=profile,
            role_name=role_name,
            role_emoji=role_emoji,
            agent_signature=signature,
            message=body,
            is_signoff=False,
            raw=msg,
        )

    # ── 会话管理 ─────────────────────────────────────────

    def _set_session(self, project_code: str, role_code: str):
        """记录活跃会话"""
        if project_code not in self._sessions:
            self._sessions[project_code] = {}
        self._sessions[project_code][role_code] = {
            "last_active": time.time(),
            "message_count": self._sessions[project_code].get(role_code, {}).get("message_count", 0) + 1,
        }

    def get_active_sessions(self) -> dict:
        """获取所有活跃会话"""
        return dict(self._sessions)

    def signoff(self, project_code: str):
        """签退项目所有会话"""
        if project_code in self._sessions:
            del self._sessions[project_code]

    # ── 回复格式化 ───────────────────────────────────────

    def format_response(self, cmd: CommandResult, content: str) -> str:
        """格式化Agent回复

        格式:
          [🏸 P1·羽球宝AI搭子] PM1-agent·开发工程师：
          收到回复，消息…
        """
        proj = cmd.project
        if not proj:
            return content

        header = f"[{proj.emoji} P{cmd.project_code[-1]}·{proj.name}] {cmd.agent_signature}："
        return f"{header}\n{content}"

    def format_signoff(self, cmd: CommandResult, summary: str = "") -> str:
        """格式化签退确认"""
        proj = cmd.project
        if not proj:
            return summary

        header = f"[{proj.emoji} P{cmd.project_code[-1]}·{proj.name}] {cmd.agent_signature}："
        if summary:
            return f"{header}\n✅ 已签退。{summary}"
        return f"{header}\n✅ 已签退，等待下一条指令。"

    # ── 帮助 ─────────────────────────────────────────────

    def help_text(self) -> str:
        """生成帮助文本"""
        lines = ["📋 **微信多Agent命令指南**", ""]
        for code in ["P1", "P2", "P3", "P4"]:
            proj = PROJECTS[code]
            lines.append(f"**{proj.emoji} {code}** — {proj.name}")
            lines.append(f"  `{code}: <消息>` → {proj.pm_name}")
            for rc, (_, rn, re) in proj.roles.items():
                if rc != "pm":
                    lines.append(f"  `{code}:{rc} <消息>` → {proj.pm_name}·{rn} {re}")
            lines.append("")
        lines.append("不加前缀 → 自动识别项目和Agent")
        return "\n".join(lines)

    # ── Dashboard 日志 ───────────────────────────────────

    def log_to_dashboard(self, cmd: CommandResult, response: str):
        """将交互记录到Dashboard日志"""
        if not self._log_path:
            return

        entry = {
            "timestamp": time.time(),
            "project": cmd.project_code,
            "project_name": cmd.project.name if cmd.project else "",
            "role": cmd.role_code,
            "agent": cmd.agent_signature,
            "profile": cmd.role_profile,
            "message": cmd.message,
            "response_preview": response[:200],
            "is_signoff": cmd.is_signoff,
        }
        try:
            log_file = self._log_path / "agent_conversations.jsonl"
            log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(log_file, "a") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass

    # ── 统计 ─────────────────────────────────────────────

    def stats(self) -> dict:
        """返回路由统计"""
        sessions = self.get_active_sessions()
        total = sum(
            s.get("message_count", 0)
            for proj_sessions in sessions.values()
            for s in proj_sessions.values()
        )
        return {
            "active_projects": len(sessions),
            "active_roles": sum(len(r) for r in sessions.values()),
            "total_messages": total,
            "sessions": {
                code: {
                    rc: {"count": s.get("message_count", 0)}
                    for rc, s in roles.items()
                }
                for code, roles in sessions.items()
            },
        }


# ── CLI 测试 ────────────────────────────────────────────

def main():
    import sys

    router = WeChatCommandRouter()

    if len(sys.argv) < 2:
        print("用法: wechat_command_router.py <消息>")
        print("      wechat_command_router.py help")
        print("      wechat_command_router.py stats")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "help":
        print(router.help_text())
        return

    if cmd == "stats":
        print(json.dumps(router.stats(), ensure_ascii=False, indent=2))
        return

    msg = " ".join(sys.argv[1:])
    result = router.parse(msg)

    print(json.dumps({
        "parsed": result.parsed,
        "project": result.project_code,
        "role": result.role_code,
        "profile": result.role_profile,
        "agent": result.agent_signature,
        "message": result.message,
        "is_signoff": result.is_signoff,
        "formatted": router.format_response(result, "→ 待执行"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
