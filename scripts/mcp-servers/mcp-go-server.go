// ════════════════════════════════════════════════════════════════
// Apex Cross-Language MCP Demo — Go MCP Server
// Exposes calculator and file analysis tools over stdio
// ════════════════════════════════════════════════════════════════
package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"math"
	"os"
	"strings"
	"time"
)

// ── MCP Protocol Types ──────────────────────────────────────────

type MCPRequest struct {
	JsonRPC string          `json:"jsonrpc"`
	ID      int             `json:"id"`
	Method  string          `json:"method"`
	Params  json.RawMessage `json:"params,omitempty"`
}

type MCPResponse struct {
	JsonRPC string      `json:"jsonrpc"`
	ID      int         `json:"id"`
	Result  interface{} `json:"result,omitempty"`
	Error   *MCPError   `json:"error,omitempty"`
}

type MCPError struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
}

type ToolParam struct {
	Type       string              `json:"type"`
	Properties map[string]Property `json:"properties"`
	Required   []string            `json:"required"`
}

type Property struct {
	Type        string   `json:"type,omitempty"`
	Description string   `json:"description,omitempty"`
	Enum        []string `json:"enum,omitempty"`
	Default     string   `json:"default,omitempty"`
}

type ToolDefinition struct {
	Name        string    `json:"name"`
	Description string    `json:"description"`
	InputSchema ToolParam `json:"inputSchema"`
}

type ToolCallParams struct {
	Name      string          `json:"name"`
	Arguments json.RawMessage `json:"arguments"`
}

type ToolResult struct {
	Content []ContentItem `json:"content"`
	IsError bool          `json:"isError"`
}

type ContentItem struct {
	Type string `json:"type"`
	Text string `json:"text"`
}

type ToolListResult struct {
	Tools []ToolDefinition `json:"tools"`
}

// ── Tool Implementations ────────────────────────────────────────

var tools = []ToolDefinition{
	{
		Name:        "calculate",
		Description: "Perform mathematical calculations — demonstrates Go MCP server",
		InputSchema: ToolParam{
			Type: "object",
			Properties: map[string]Property{
				"expression": {Type: "string", Description: "Mathematical expression to evaluate (e.g., '2 + 2', 'sin(45)', 'sqrt(16)')"},
			},
			Required: []string{"expression"},
		},
	},
	{
		Name:        "file_analysis",
		Description: "Analyze a file on the server filesystem — demonstrates Go's system access",
		InputSchema: ToolParam{
			Type: "object",
			Properties: map[string]Property{
				"path": {Type: "string", Description: "Absolute path to the file to analyze"},
			},
			Required: []string{"path"},
		},
	},
	{
		Name:        "current_time",
		Description: "Get the current server time in any timezone — demonstrates Go's time library",
		InputSchema: ToolParam{
			Type: "object",
			Properties: map[string]Property{
				"timezone": {
					Type:        "string",
					Description: "Timezone (e.g., 'Asia/Shanghai', 'America/New_York', 'UTC')",
					Default:     "UTC",
				},
			},
			Required: []string{},
		},
	},
}

func safeEval(expr string) string {
	// Safety: only allow basic math operations
	// This is a demo — not a full expression parser
	expr = strings.TrimSpace(expr)

	// Simple calculator using basic operations
	var a, b float64
	var op string
	n, _ := fmt.Sscanf(expr, "%f %s %f", &a, &op, &b)
	if n == 3 {
		switch op {
		case "+":
			return fmt.Sprintf("%.4f", a+b)
		case "-":
			return fmt.Sprintf("%.4f", a-b)
		case "*", "×":
			return fmt.Sprintf("%.4f", a*b)
		case "/", "÷":
			if b == 0 {
				return "Error: Division by zero"
			}
			return fmt.Sprintf("%.4f", a/b)
		case "^", "**":
			return fmt.Sprintf("%.4f", math.Pow(a, b))
		}
	}

	// Check for built-in functions
	if strings.HasPrefix(expr, "sqrt(") && strings.HasSuffix(expr, ")") {
		var v float64
		fmt.Sscanf(expr, "sqrt(%f)", &v)
		if v < 0 {
			return "Error: Cannot calculate sqrt of negative number"
		}
		return fmt.Sprintf("%.4f", math.Sqrt(v))
	}
	if strings.HasPrefix(expr, "sin(") && strings.HasSuffix(expr, ")") {
		var v float64
		fmt.Sscanf(expr, "sin(%f)", &v)
		return fmt.Sprintf("%.4f", math.Sin(v*math.Pi/180))
	}
	if strings.HasPrefix(expr, "cos(") && strings.HasSuffix(expr, ")") {
		var v float64
		fmt.Sscanf(expr, "cos(%f)", &v)
		return fmt.Sprintf("%.4f", math.Cos(v*math.Pi/180))
	}
	if strings.HasPrefix(expr, "abs(") && strings.HasSuffix(expr, ")") {
		var v float64
		fmt.Sscanf(expr, "abs(%f)", &v)
		return fmt.Sprintf("%.4f", math.Abs(v))
	}
	if expr == "pi" || expr == "π" {
		return fmt.Sprintf("%.6f", math.Pi)
	}
	if expr == "e" {
		return fmt.Sprintf("%.6f", math.E)
	}

	return fmt.Sprintf("Unsupported expression: %s\nSupported: a + b, a - b, a * b, a / b, a ^ b, sqrt(x), sin(x), cos(x), pi, e", expr)
}

func handleToolCall(name string, rawArgs json.RawMessage) ToolResult {
	switch name {
	case "calculate":
		var args struct {
			Expression string `json:"expression"`
		}
		json.Unmarshal(rawArgs, &args)
		result := safeEval(args.Expression)
		return ToolResult{
			Content: []ContentItem{{Type: "text", Text: result}},
			IsError: strings.HasPrefix(result, "Error") || strings.HasPrefix(result, "Unsupported"),
		}

	case "file_analysis":
		var args struct {
			Path string `json:"path"`
		}
		json.Unmarshal(rawArgs, &args)
		info, err := os.Stat(args.Path)
		if err != nil {
			return ToolResult{
				Content: []ContentItem{{Type: "text", Text: fmt.Sprintf("Error accessing file: %v", err)}},
				IsError: true,
			}
		}
		analysis := fmt.Sprintf(`File Analysis (via Go MCP Server):
  Path: %s
  Size: %d bytes
  Mode: %s
  Modified: %s
  Is Directory: %v`,
			args.Path, info.Size(), info.Mode(), info.ModTime().Format(time.RFC3339), info.IsDir())
		return ToolResult{
			Content: []ContentItem{{Type: "text", Text: analysis}},
			IsError: false,
		}

	case "current_time":
		var args struct {
			Timezone string `json:"timezone"`
		}
		json.Unmarshal(rawArgs, &args)
		if args.Timezone == "" {
			args.Timezone = "UTC"
		}
		loc, err := time.LoadLocation(args.Timezone)
		if err != nil {
			return ToolResult{
				Content: []ContentItem{{Type: "text", Text: fmt.Sprintf("Unknown timezone: %s", args.Timezone)}},
				IsError: true,
			}
		}
		now := time.Now().In(loc)
		result := fmt.Sprintf(`Current Time (via Go MCP Server):
  Timezone: %s
  Time: %s
  Date: %s
  Unix: %d`,
			args.Timezone, now.Format("15:04:05"), now.Format("2006-01-02"), now.Unix())
		return ToolResult{
			Content: []ContentItem{{Type: "text", Text: result}},
			IsError: false,
		}

	default:
		return ToolResult{
			Content: []ContentItem{{Type: "text", Text: fmt.Sprintf("Unknown Go tool: %s", name)}},
			IsError: true,
		}
	}
}

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	encoder := json.NewEncoder(os.Stdout)

	// Signal ready
	encoder.Encode(map[string]interface{}{
		"jsonrpc": "2.0",
		"method":  "server/ready",
		"params": map[string]string{
			"name":    "Go MCP Server",
			"version": "1.0.0",
		},
	})

	for scanner.Scan() {
		line := scanner.Text()
		var req MCPRequest
		if err := json.Unmarshal([]byte(line), &req); err != nil {
			continue
		}

		switch req.Method {
		case "tools/list":
			encoder.Encode(MCPResponse{
				JsonRPC: "2.0",
				ID:      req.ID,
				Result: ToolListResult{Tools: tools},
			})

		case "tools/call":
			var params ToolCallParams
			json.Unmarshal(req.Params, &params)
			result := handleToolCall(params.Name, params.Arguments)
			encoder.Encode(MCPResponse{
				JsonRPC: "2.0",
				ID:      req.ID,
				Result:  result,
			})

		case "initialize":
			encoder.Encode(MCPResponse{
				JsonRPC: "2.0",
				ID:      req.ID,
				Result: map[string]interface{}{
					"protocolVersion": "0.1.0",
					"capabilities":    map[string]interface{}{"tools": struct{}{}},
					"serverInfo": map[string]string{
						"name":    "apex-go-mcp",
						"version": "1.0.0",
					},
				},
			})

		case "server/info":
			encoder.Encode(MCPResponse{
				JsonRPC: "2.0",
				ID:      req.ID,
				Result: map[string]interface{}{
					"name":     "Go MCP Server",
					"version":  "1.0.0",
					"language": "go",
					"runtime":  "go1.23",
					"tools":    []string{"calculate", "file_analysis", "current_time"},
				},
			})

		default:
			encoder.Encode(MCPResponse{
				JsonRPC: "2.0",
				ID:      req.ID,
				Error:   &MCPError{Code: -32601, Message: "Method not found: " + req.Method},
			})
		}
	}
}
