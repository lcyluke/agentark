<p align="center">
  <strong>⚡ Apex — 多Agent操作系统</strong><br>
  <em>让一个人拥有一个公司的能力。</em>
</p>

<p align="center">
  <a href="https://github.com/lcyluke/apex/stargazers"><img src="https://img.shields.io/github/stars/lcyluke/apex?style=social" alt="Stars"></a>
  <a href="https://github.com/lcyluke/apex/network/members"><img src="https://img.shields.io/github/forks/lcyluke/apex?style=social" alt="Forks"></a>
  <a href="https://github.com/lcyluke/apex/watchers"><img src="https://img.shields.io/github/watchers/lcyluke/apex?style=social" alt="Watchers"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.10%2B-orange?style=flat-square" alt="Python"></a>
</p>

<p align="center">
  <a href="#-快速开始">快速开始</a>
  · <a href="#-核心创新">核心创新</a>
  · <a href="#-编排模式">编排模式</a>
  · <a href="#-命令大全">命令</a>
  · <a href="#-安装">安装</a>
</p>

---

## 🚀 快速开始

```bash
pip install apex-multiagent
apex init my-project && cd my-project
apex run "写一个登录页面"
apex run "开发一个完整网站" --swarm
apex crew create "设计一个社交应用" --members pm,frontend,backend
apex company create 羽球宝AI -i saas
apex dashboard
```

---

## 🏆 核心创新

| # | 创新 | 一句话 |
|---|------|--------|
| 1 | **动态技能进化** | Agent从每次执行中学习，100次后错误率降90%+ |
| 2 | **零点击组队** | 一句话，Apex自动设计最优团队 |
| 3 | **自愈工作流** | 三振出局：重试→换模型→简化→通知人 |
| 4 | **知识图谱记忆** | 教会一个Agent=教会所有Agent |
| 5 | **Token预算银行** | 智能路由按任务价值选模型，省95%费用 |
| 6 | **MCP全家桶** | 跨语言跨框架，Python↔Java↔Rust无缝协作 |
| 7 | **One-Click Company** | 一行命令创建AI公司 |

---

## 🔄 编排模式

| 场景 | 模式 | 命令 |
|------|------|------|
| 软件开发 | Crew + Chain | `apex crew create "开发Web应用"` |
| 研究分析 | Debate | `apex debate "该用微服务吗？"` |
| 内容生产 | Chain | `apex chain run "写一篇博客" -p content` |
| 客户支持 | Router | `apex router route "我的账号被锁了"` |
| 企业审批 | Supervisor | `apex supervisor "设计合规流程"` |
| DevOps监控 | Monitor | `apex monitor check -f /var/log/nginx.log` |
| 产品策略 | Swarm | `apex run "分析市场竞争" --swarm` |
| 初创公司 | Company | `apex company create my-startup -i saas` |

---

## 📋 命令大全

| 命令 | 说明 |
|------|------|
| `apex init <name>` | 初始化项目 |
| `apex run "<task>"` | 单Agent执行 |
| `apex run "<task>" --swarm` | Swarm模式 |
| `apex crew create "<goal>"` | Crew模式 |
| `apex chain run "<goal>" -p dev` | 流水线模式 |
| `apex debate "<topic>"` | 辩论模式 |
| `apex router route "<task>"` | 路由模式 |
| `apex supervisor "<goal>"` | 审批模式 |
| `apex monitor check -f <file>` | 监控模式 |
| `apex team create <name>` | 创建Agent |
| `apex template list` | 模板列表 |
| `apex template use <name>` | 从模板创建 |
| `apex economy status` | 经济看板 |
| `apex knowledge query "<q>"` | 知识图谱查询 |
| `apex evolution agent <name>` | Agent进化报告 |
| `apex company create <name>` | 创建AI公司 |
| `apex autonomous start` | 启动7x24引擎 |
| `apex dashboard` | Web UI |

---

## 📥 安装

```bash
# macOS / Linux / Windows
pip install apex-multiagent

# 配置API Key
export DEEPSEEK_API_KEY="sk-xxx"
```

详见 [English README](README.md) 的安装章节。

---

## 🤝 参与贡献

```bash
git clone https://github.com/lcyluke/apex.git && cd apex
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,web]"
pytest tests/ -v
```

---

<p align="center">
  <strong>⚡ 从今天开始，一个人就是一个公司。</strong>
  <br>
  <a href="https://github.com/lcyluke/apex">GitHub</a> · <a href="https://github.com/lcyluke/apex/issues">Issues</a>
</p>
