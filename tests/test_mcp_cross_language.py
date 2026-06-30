"""Cross-language MCP integration test — Apex ↔ Node.js ↔ Go ↔ Rust.

Validates the full MCP stdio transport protocol:
  1. Launch external MCP servers (Node.js/Go/Rust) as subprocesses
  2. Connect via MCP stdio client (JSON-RPC over stdin/stdout)
  3. List tools from each server
  4. Call tools on each server with different arguments
  5. Register all tools into the Apex MCP Hub
  6. Verify round-trip cross-language communication
"""
import os
import sys
import json
import time
from pathlib import Path

# ── Setup ──────────────────────────────────────────────────────

APEX_DIR = Path(os.environ.get("APEX_DIR", "/Users/Mac/Desktop/2026AIAPP/Apex"))
SCRIPTS_DIR = APEX_DIR / "scripts" / "mcp-servers"
sys.path.insert(0, str(APEX_DIR))

from agentark.mcp.stdio_client import MCPStdioClient
from agentark.mcp.hub import MCPHub

passed = 0
failed = 0

def section(title):
    print(f"\n{'='*65}")
    print(f"  {title}")
    print(f"{'='*65}")

def check(name, result, detail=""):
    global passed, failed
    if result:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}: {detail}")

# ═══════════════════════════════════════════════════════════════
# 1. Node.js MCP Server
# ═══════════════════════════════════════════════════════════════

section("1. 🟢 Node.js MCP Server — Cross-Language Test")

node_server = MCPStdioClient(
    command="node",
    args=[str(SCRIPTS_DIR / "mcp-node-server.js")],
    name="Node.js",
)

try:
    connected = node_server.connect(timeout=5)
    check("connect() to Node.js server", connected)

    if connected:
        # List tools
        tools = node_server.list_tools()
        check(f"list_tools() — {len(tools)} tools found", len(tools) >= 3)
        tool_names = [t["name"] for t in tools]
        check("'greet' tool available", "greet" in tool_names, tool_names)
        check("'weather' tool available", "weather" in tool_names, tool_names)
        check("'analyze_sentiment' tool available", "analyze_sentiment" in tool_names, tool_names)

        # Call tools
        result = node_server.call_tool("greet", {"name": "Luke", "language": "zh"})
        text = "".join(c.get("text", "") for c in result.get("content", []))
        check("greet('Luke', 'zh') returns Chinese", "Luke" in text and "你好" in text, text)

        result = node_server.call_tool("weather", {"city": "Shenzhen"})
        text = "".join(c.get("text", "") for c in result.get("content", []))
        check("weather('Shenzhen') returns data", "28" in text and "Sunny" in text, text[:50])

        result = node_server.call_tool("analyze_sentiment", {"text": "This is absolutely wonderful and amazing!"})
        content = "".join(c.get("text", "") for c in result.get("content", []))
        data = json.loads(content)
        check("analyze_sentiment() returns positive", data["sentiment"] == "positive", content[:80])

        # Get server info
        info = node_server.get_server_info()
        check(f"server/info: language={info.get('language')}", info.get("language") == "javascript", str(info))

        print(f"\n  🌐 Node.js -> Python MCP round-trip: ✅ confirmed")

    node_server.disconnect()
    check("disconnect() cleanup", not node_server.is_running)

except Exception as e:
    check("Node.js MCP test", False, str(e)[:120])
    node_server.disconnect()

# ═══════════════════════════════════════════════════════════════
# 2. Go MCP Server
# ═══════════════════════════════════════════════════════════════

section("2. 🔵 Go MCP Server — Cross-Language Test")

go_server = MCPStdioClient(
    command=str(SCRIPTS_DIR / "mcp-go-server"),
    args=[],
    name="Go",
)

try:
    connected = go_server.connect(timeout=5)
    check("connect() to Go server", connected)

    if connected:
        tools = go_server.list_tools()
        check(f"list_tools() — {len(tools)} tools found", len(tools) >= 3)
        tool_names = [t["name"] for t in tools]
        check("'calculate' tool available", "calculate" in tool_names, tool_names)
        check("'file_analysis' tool available", "file_analysis" in tool_names, tool_names)
        check("'current_time' tool available", "current_time" in tool_names, tool_names)

        # Test calculator
        result = go_server.call_tool("calculate", {"expression": "2 + 2"})
        text = "".join(c.get("text", "") for c in result.get("content", []))
        check("calculate(2 + 2) = 4", "4.0000" in text, text)

        result = go_server.call_tool("calculate", {"expression": "sin(90)"})
        text = "".join(c.get("text", "") for c in result.get("content", []))
        check("calculate(sin(90)) = 1", "1.0000" in text, text)

        result = go_server.call_tool("calculate", {"expression": "pi"})
        text = "".join(c.get("text", "") for c in result.get("content", []))
        check("calculate(pi) = 3.14...", "3.14159" in text, text)

        # Test file analysis
        test_file = str(SCRIPTS_DIR / "mcp-go-server.go")
        result = go_server.call_tool("file_analysis", {"path": test_file})
        text = "".join(c.get("text", "") for c in result.get("content", []))
        check("file_analysis() returns file data", "Go MCP Server" in text and "Size:" in text, text[:50])

        # Test time
        result = go_server.call_tool("current_time", {"timezone": "Asia/Shanghai"})
        text = "".join(c.get("text", "") for c in result.get("content", []))
        check("current_time(Asia/Shanghai) returns time", "Timezone:" in text and "Asia/Shanghai" in text, text[:50])

        # Get server info
        info = go_server.get_server_info()
        check(f"server/info: language={info.get('language')}", info.get("language") == "go", str(info))

        print(f"\n  🌐 Go -> Python MCP round-trip: ✅ confirmed")

    go_server.disconnect()
    check("disconnect() cleanup", not go_server.is_running)

except Exception as e:
    check("Go MCP test", False, str(e)[:120])
    go_server.disconnect()

# ═══════════════════════════════════════════════════════════════
# 3. Rust MCP Server (zero deps)
# ═══════════════════════════════════════════════════════════════

section("3. 🟠 Rust MCP Server — Cross-Language Test (zero external deps)")

rust_server = MCPStdioClient(
    command=str(SCRIPTS_DIR / "mcp-rust-server"),
    args=[],
    name="Rust",
)

try:
    connected = rust_server.connect(timeout=5)
    check("connect() to Rust server", connected)

    if connected:
        tools = rust_server.list_tools()
        check(f"list_tools() — {len(tools)} tools found", len(tools) >= 3)
        tool_names = [t["name"] for t in tools]
        check("'analyze_text' tool available", "analyze_text" in tool_names, tool_names)
        check("'fibonacci' tool available", "fibonacci" in tool_names, tool_names)
        check("'prime_factors' tool available", "prime_factors" in tool_names, tool_names)

        # Test text analysis
        test_text = "Rust is great and fast and safe and amazing!"
        result = rust_server.call_tool("analyze_text", {"text": test_text})
        content = "".join(c.get("text", "") for c in result.get("content", []))
        data = json.loads(content)
        check(f"analyze_text() — {data['word_count']} words", data["word_count"] == 8, str(data))

        # Test fibonacci
        result = rust_server.call_tool("fibonacci", {"n": 20})
        content = "".join(c.get("text", "") for c in result.get("content", []))
        data = json.loads(content)
        check("fibonacci(20) = 6765", "F(20) = 6765" in data["result"], content[:60])

        # Test prime factors
        result = rust_server.call_tool("prime_factors", {"n": 84})
        content = "".join(c.get("text", "") for c in result.get("content", []))
        data = json.loads(content)
        check("prime_factors(84) = [2,2,3,7]", data["prime_factors"] == [2, 2, 3, 7], str(data))

        # Get server info
        info = rust_server.get_server_info()
        check(f"server/info: language={info.get('language')}", info.get("language") == "rust", str(info))

        print(f"\n  🌐 Rust -> Python MCP round-trip: ✅ confirmed")

    rust_server.disconnect()
    check("disconnect() cleanup", not rust_server.is_running)

except Exception as e:
    check("Rust MCP test", False, str(e)[:120])
    rust_server.disconnect()

# ═══════════════════════════════════════════════════════════════
# 4. ALL-IN-ONE: Register all 3 servers into Apex MCP Hub
# ═══════════════════════════════════════════════════════════════

section("4. 🔗 Unified MCP Hub — All 3 Languages Registered Together")

hub = MCPHub()
# Hub already has built-in tools: filesystem, shell, knowledge, http
builtin_count = len(hub.list_tools())
check(f"Hub has {builtin_count} built-in tools", builtin_count >= 4)

# Launch all three servers and register their tools
servers = []
prefixes = {"node": "node.", "go": "go.", "rust": "rust."}
server_configs = [
    ("node", "node", [str(SCRIPTS_DIR / "mcp-node-server.js")]),
    ("go", str(SCRIPTS_DIR / "mcp-go-server"), []),
    ("rust", str(SCRIPTS_DIR / "mcp-rust-server"), []),
]

all_ok = True
for name, cmd, args in server_configs:
    try:
        s = MCPStdioClient(command=cmd, args=args, name=name)
        if s.connect(timeout=5):
            s.register_with_hub(hub, prefix=f"{name}.")
            servers.append(s)
            check(f"Registered {name} tools into Hub", True)
        else:
            check(f"Connect {name}", False, "timeout")
            all_ok = False
    except Exception as e:
        check(f"Register {name}", False, str(e)[:60])
        all_ok = False

# Count all tools in hub
all_tools = hub.list_tools()
tool_names = [t["name"] for t in all_tools]
prefixed = [n for n in tool_names if "." in n]
check(f"Hub has {len(all_tools)} total tools ({len(prefixed)} cross-language)",
      len(prefixed) >= 9, str(tool_names))

# Verify specific tools from each language
check("node.greet available", "node.greet" in tool_names)
check("go.calculate available", "go.calculate" in tool_names)
check("rust.analyze_text available", "rust.analyze_text" in tool_names)

# Call a cross-language tool through the Hub
result = hub.call("node.greet", name="Apex", language="en")
check("Hub.call(node.greet) works", result.success and "Apex" in result.output, result.output[:60])

result = hub.call("go.calculate", expression="sqrt(16)")
check("Hub.call(go.calculate) works", result.success and "4.0000" in result.output, result.output[:20])

result = hub.call("rust.analyze_text", text="Hello world from Apex!")
check("Hub.call(rust.analyze_text) works", result.success and "word_count" in result.output, result.output[:60])

# Disconnect all
for s in servers:
    s.disconnect()

# ═══════════════════════════════════════════════════════════════
# RESULTS
# ═══════════════════════════════════════════════════════════════

total = passed + failed
print(f"\n{'='*65}")
print(f"  CROSS-LANGUAGE MCP INTEGRATION TEST RESULTS")
print(f"{'='*65}")
print(f"\n  ✅ Passed: {passed}/{total} ({passed/total*100:.1f}%)")
print(f"  ❌ Failed: {failed}/{total}")
print(f"\n  Languages tested: Python ↔ Node.js ↔ Go ↔ Rust")
print(f"  Protocol: JSON-RPC 2.0 over stdio (MCP)")
print(f"  Total tools across all languages: {len(all_tools)}")
print(f"  Cross-language tools: {len(prefixed)}")
print(f"\n  {'🎉 ALL PASSED — Cross-language MCP is fully operational!' if failed == 0 else '⚠️  Some tests failed'}")
print(f"{'='*65}")
