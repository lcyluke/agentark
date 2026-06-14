老卢（始祖agent）是Apex多Agent项目总设计师。沟通语言：中文。期望：结构化输出、清晰决策框架、分类合理的功能架构、实时资源监控、项目制Agent委派、人和Agent角色分离（董事会+CEO+授权+审计）、PM/创始人保留审批权。作风：直接、抓核心、反感过度工程和不必要的修改。
§
老卢的沟通风格：极度简洁直接，常用单字/单词指令，讨厌冗长解释和铺垫。回复时用最短路径，直接执行不废话。
§
老卢（始祖agent/Origin Agent）是 Apex 多Agent操作系统的总设计师和创建者。沟通语言：中文，偏好直接带方案的回复。

项目根路径：/Users/Mac/Desktop/2026AIAPP/Apex
启动命令：.venv/bin/python -m apex dashboard --port 8080
Hermes profile 会话路径：~/.hermes/profiles/frontend-dev/

DeepSeek API Key 存储在 macOS 钥匙串（service "hermes"），有效未过期。新 Hermes profile 需从 keychain 读取 key 或复制 frontend-dev 的 config.yaml 来继承 provider: deepseek 配置。

关键成果：
- Command Center (/cc)：10视图+5交互模块，2408行，command_center.html
- apex chat 命令：CLI + chat_cmds.py，23个Agent可一键启动
- task-delegation-governance skill：6条指派规则+5态流转+上下文包
- .apex/project_context.md：Agent共享的项目上下文
- 6个Apex Profile、11个任务、3个团队已创建