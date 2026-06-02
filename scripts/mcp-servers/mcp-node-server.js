/**
 * Apex Cross-Language MCP Demo — Node.js MCP Server
 * 
 * MCP (Model Context Protocol) server over stdio.
 * Exposes tools that can be called by Apex agents via MCP Hub.
 * 
 * Usage: node mcp-node-server.js
 */
const readline = require('readline');

const TOOLS = [
  {
    name: "greet",
    description: "Greet a user in multiple languages — demonstrates Node.js as MCP tool provider",
    inputSchema: {
      type: "object",
      properties: {
        name: { type: "string", description: "Name of the person to greet" },
        language: { type: "string", enum: ["en", "zh", "ja", "ko", "fr"], default: "en", description: "Language code" },
      },
      required: ["name"],
    },
  },
  {
    name: "weather",
    description: "Get simulated weather for a city — demonstrates Node.js capability",
    inputSchema: {
      type: "object",
      properties: {
        city: { type: "string", description: "City name" },
      },
      required: ["city"],
    },
  },
  {
    name: "analyze_sentiment",
    description: "Analyze sentiment of text — demonstrates Node.js NLP-like tool",
    inputSchema: {
      type: "object",
      properties: {
        text: { type: "string", description: "Text to analyze" },
      },
      required: ["text"],
    },
  },
];

const GREETINGS = {
  en: (name) => `Hello, ${name}! Welcome from the Node.js MCP Server.`,
  zh: (name) => `你好，${name}！来自 Node.js MCP 服务器的问候。`,
  ja: (name) => `こんにちは、${name}！Node.js MCPサーバーからのご挨拶です。`,
  ko: (name) => `안녕하세요, ${name}! Node.js MCP 서버에서 인사드립니다.`,
  fr: (name) => `Bonjour, ${name}! Bienvenue du serveur MCP Node.js.`,
};

const WEATHER_DATA = {
  "shenzhen": { temp: 28, humidity: 75, condition: "☀️ Sunny", wind: "12 km/h" },
  "beijing": { temp: 22, humidity: 40, condition: "⛅ Partly Cloudy", wind: "8 km/h" },
  "tokyo": { temp: 18, humidity: 65, condition: "🌧️ Light Rain", wind: "15 km/h" },
  "new york": { temp: 15, humidity: 55, condition: "☁️ Cloudy", wind: "20 km/h" },
  "london": { temp: 12, humidity: 80, condition: "🌧️ Drizzle", wind: "18 km/h" },
};

function handleToolCall(name, args) {
  switch (name) {
    case "greet": {
      const greeting = GREETINGS[args.language || "en"] || GREETINGS.en;
      const message = greeting(args.name);
      return {
        content: [{ type: "text", text: message }],
        isError: false,
      };
    }
    case "weather": {
      const city = (args.city || "").toLowerCase();
      const data = WEATHER_DATA[city];
      if (!data) {
        return {
          content: [{ type: "text", text: JSON.stringify({
            city: args.city,
            error: `No weather data for '${args.city}'. Available: ${Object.keys(WEATHER_DATA).join(", ")}`,
          }, null, 2) }],
          isError: true,
        };
      }
      return {
        content: [{ type: "text", text: JSON.stringify({ city: args.city, ...data }, null, 2) }],
        isError: false,
      };
    }
    case "analyze_sentiment": {
      const text = args.text || "";
      const positiveWords = ["good", "great", "excellent", "happy", "love", "wonderful", "amazing", "beautiful", "fantastic", "nice", "best", "awesome"];
      const negativeWords = ["bad", "terrible", "awful", "hate", "horrible", "worst", "sad", "angry", "ugly", "poor", "crappy", "disgusting"];
      const lower = text.toLowerCase();
      const posCount = positiveWords.filter(w => lower.includes(w)).length;
      const negCount = negativeWords.filter(w => lower.includes(w)).length;
      const total = posCount + negCount;
      let sentiment = "neutral";
      let score = 0.5;
      if (total > 0) {
        score = posCount / total;
        if (score > 0.6) sentiment = "positive";
        else if (score < 0.4) sentiment = "negative";
      }
      return {
        content: [{ type: "text", text: JSON.stringify({
          text: text.substring(0, 100),
          sentiment,
          score: Math.round(score * 100) / 100,
          positive_words: posCount,
          negative_words: negCount,
          language: "node.js",
        }, null, 2) }],
        isError: false,
      };
    }
    default:
      return {
        content: [{ type: "text", text: `Unknown tool: ${name}` }],
        isError: true,
      };
  }
}

// ═══════════════════════════════════════════
// MCP stdio Protocol — JSON-RPC 2.0
// ═══════════════════════════════════════════

const rl = readline.createInterface({ input: process.stdin });

rl.on("line", (line) => {
  try {
    const msg = JSON.parse(line);
    const id = msg.id;

    if (msg.method === "tools/list") {
      const response = {
        jsonrpc: "2.0",
        id,
        result: { tools: TOOLS },
      };
      process.stdout.write(JSON.stringify(response) + "\n");
    } 
    else if (msg.method === "tools/call") {
      const toolName = msg.params.name;
      const args = msg.params.arguments || {};
      const result = handleToolCall(toolName, args);
      const response = {
        jsonrpc: "2.0",
        id,
        result,
      };
      process.stdout.write(JSON.stringify(response) + "\n");
    }
    else if (msg.method === "initialize") {
      const response = {
        jsonrpc: "2.0",
        id,
        result: {
          protocolVersion: "0.1.0",
          capabilities: {
            tools: {},
          },
          serverInfo: {
            name: "apex-nodejs-mcp",
            version: "1.0.0",
          },
        },
      };
      process.stdout.write(JSON.stringify(response) + "\n");
    }
    else if (msg.method === "server/info") {
      const response = {
        jsonrpc: "2.0",
        id,
        result: {
          name: "Node.js MCP Server",
          version: "1.0.0",
          language: "javascript",
          runtime: process.version,
          tools: TOOLS.map(t => t.name),
        },
      };
      process.stdout.write(JSON.stringify(response) + "\n");
    }
    else {
      const response = {
        jsonrpc: "2.0",
        id,
        error: { code: -32601, message: `Method not found: ${msg.method}` },
      };
      process.stdout.write(JSON.stringify(response) + "\n");
    }
  } catch (e) {
    // Ignore parse errors
  }
});

// Signal ready
process.stdout.write(JSON.stringify({
  jsonrpc: "2.0",
  method: "server/ready",
  params: { name: "Node.js MCP Server", version: "1.0.0" },
}) + "\n");
