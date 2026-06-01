# Apex — <Show HN> 我花4小时写了全世界最好的多Agent框架

> 一个命令创建AI公司，3分钟上手，智能路由省95%费用。

之前做多Agent项目时发现一个严重问题：现有框架（CrewAI / LangGraph / AutoGen / CAMEL / MetaGPT）每个都只解决一个问题。

**要跑一个多Agent项目，你需要：**
- CrewAI 负责角色分工
- LangGraph 负责状态控制
- LangSmith 负责监控
- CAMEL 负责Agent学习
- 再加几个工具处理记忆、Token控制、MCP...

**于是我自己写了Apex — 多Agent操作系统。**

## 🏆 7大创新

1. **动态技能进化** — Agent从每次执行中学习，越用越聪明
2. **零点击组队** — 一句话自动设计团队
3. **自愈工作流** — 三振出局+自动降级+知识积累
4. **知识图谱记忆** — 图结构+跨Agent共享+自动推理
5. **Token预算银行** — 智能路由按任务价值选模型，省95%费用
6. **MCP全家桶** — 跨语言跨框架协作
7. **One-Click Company** — 一行命令创建AI公司

## 🚀 体验

```bash
pip install apex
apex init my-project
apex run "写一个登录页面"
apex crew create "设计社交应用" --members pm,frontend,backend
apex company create my-startup -i saas
apex company start my-startup "Build MVP"
apex dashboard  # Web UI监控面板
```

## 📊 9组CLI命令 + 5个内置模板 + Web UI

开源MIT，欢迎一起搞。

GitHub: https://github.com/luke/apex

从今天开始，一个人就是一个公司。⚡
