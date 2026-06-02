// ════════════════════════════════════════════════════════════════
// Apex Cross-Language MCP Demo — Rust MCP Server (no deps)
// Pure Rust with no external crates — just stdlib JSON building
// ════════════════════════════════════════════════════════════════
use std::io::{self, BufRead, Write};
use std::collections::HashSet;

fn json_str(s: &str) -> String {
    format!("\"{}\"", s.replace('\\', "\\\\").replace('"', "\\\"").replace('\n', "\\n"))
}

fn json_number(n: f64) -> String {
    if n.fract() == 0.0 {
        format!("{}", n as i64)
    } else {
        format!("{:.2}", n)
    }
}

fn json_object(entries: Vec<(&str, String)>) -> String {
    let pairs: Vec<String> = entries.iter()
        .map(|(k, v)| format!("{}:{}", json_str(k), v))
        .collect();
    format!("{{{}}}", pairs.join(","))
}

fn json_array(items: Vec<String>) -> String {
    format!("[{}]", items.join(","))
}

fn respond(id: u64, result: &str) {
    let resp = format!("{{\"jsonrpc\":\"2.0\",\"id\":{},\"result\":{}}}", id, result);
    println!("{}", resp);
    io::stdout().flush().unwrap();
}

fn respond_error(id: u64, code: i64, msg: &str) {
    let resp = format!(
        "{{\"jsonrpc\":\"2.0\",\"id\":{},\"error\":{{\"code\":{},\"message\":{}}}}}",
        id, code, json_str(msg)
    );
    println!("{}", resp);
    io::stdout().flush().unwrap();
}

fn respond_text(id: u64, text: &str, is_error: bool) {
    let content = format!("{{\"type\":\"text\",\"text\":{}}}", json_str(text));
    let result = json_object(vec![
        ("content", json_array(vec![content])),
        ("isError", if is_error { "true".to_string() } else { "false".to_string() }),
    ]);
    respond(id, &result);
}

fn analyze_text(text: &str) -> String {
    let words: Vec<&str> = text.split_whitespace().collect();
    let chars = text.chars().count();
    let sentences: Vec<&str> = text
        .split(|c: char| c == '.' || c == '!' || c == '?')
        .map(|s| s.trim())
        .filter(|s| !s.is_empty())
        .collect();
    let avg_word_len = if words.is_empty() { 0.0 } else { chars as f64 / words.len() as f64 };
    let unique: HashSet<String> = words.iter().map(|w| w.to_lowercase()).collect();
    let richness = if words.is_empty() { 0.0 } else { unique.len() as f64 / words.len() as f64 };

    json_object(vec![
        ("word_count", json_number(words.len() as f64)),
        ("char_count", json_number(chars as f64)),
        ("sentence_count", json_number(sentences.len() as f64)),
        ("avg_word_length", json_number(avg_word_len)),
        ("unique_words", json_number(unique.len() as f64)),
        ("vocabulary_richness", json_number(richness)),
        ("language", json_str("rust")),
    ])
}

fn fibonacci(n: u64) -> String {
    if n == 0 { return json_str("0"); }
    if n == 1 { return json_str("1"); }
    let (mut a, mut b): (u128, u128) = (0, 1);
    for _ in 2..=n.min(100) {
        let c = a + b;
        a = b;
        b = c;
    }
    json_str(&format!("F({}) = {}", n, b))
}

fn prime_factors(n: u64) -> String {
    let mut num = n;
    let mut factors = Vec::new();
    let mut i = 2;
    while i * i <= num {
        while num % i == 0 {
            factors.push(i);
            num /= i;
        }
        i += 1;
    }
    if num > 1 { factors.push(num); }
    let factors_json: Vec<String> = factors.iter().map(|f| json_number(*f as f64)).collect();
    json_object(vec![
        ("number", json_number(n as f64)),
        ("prime_factors", json_array(factors_json)),
        ("is_prime", if factors.len() == 1 && factors[0] == n { "true".to_string() } else { "false".to_string() }),
        ("language", json_str("rust")),
    ])
}

fn handle_tool_call(id: u64, name: &str, params_str: &str) {
    match name {
        "analyze_text" => {
            // Crude JSON parse: find "text":"..." 
            if let Some(start) = params_str.find("\"text\":\"") {
                let after = &params_str[start + 8..];
                if let Some(end) = after.find('"') {
                    let text = &after[..end];
                    let result = analyze_text(&text.replace("\\\"", "\"").replace("\\n", "\n"));
                    respond(id, &result);
                    return;
                }
            }
            respond_text(id, "Error: 'text' parameter required or malformed", true);
        }
        "fibonacci" => {
            if let Some(start) = params_str.find("\"n\":") {
                let after = &params_str[start + 4..];
                let num_str: String = after.chars().take_while(|c| c.is_ascii_digit()).collect();
                if let Ok(n) = num_str.parse::<u64>() {
                    if n > 100 {
                        respond_text(id, "Error: n must be <= 100", true);
                        return;
                    }
                    let result = json_object(vec![
                        ("result", fibonacci(n)),
                        ("language", json_str("rust")),
                    ]);
                    respond(id, &result);
                    return;
                }
            }
            respond_text(id, "Error: 'n' parameter required or malformed", true);
        }
        "prime_factors" => {
            if let Some(start) = params_str.find("\"n\":") {
                let after = &params_str[start + 4..];
                let num_str: String = after.chars().take_while(|c| c.is_ascii_digit()).collect();
                if let Ok(n) = num_str.parse::<u64>() {
                    if n < 2 {
                        respond_text(id, "Error: n must be >= 2", true);
                        return;
                    }
                    respond(id, &prime_factors(n));
                    return;
                }
            }
            respond_text(id, "Error: 'n' parameter required or malformed", true);
        }
        _ => respond_error(id, -32601, &format!("Unknown tool: {}", name)),
    }
}

fn main() {
    // Signal ready
    println!("{{\"jsonrpc\":\"2.0\",\"method\":\"server/ready\",\"params\":{{\"name\":\"Rust MCP Server\",\"version\":\"1.0.0\"}}}}");
    io::stdout().flush().unwrap();

    let stdin = io::stdin();
    for line in stdin.lock().lines() {
        let line = match line { Ok(l) => l, Err(_) => break };
        if line.trim().is_empty() { continue; }

        // Simplified JSON-RPC parsing (no serde dependency)
        let id = line.split("\"id\":")
            .nth(1)
            .and_then(|s| s.chars().take_while(|c| c.is_ascii_digit()).collect::<String>().parse::<u64>().ok())
            .unwrap_or(0);

        if line.contains("\"method\":\"tools/list\"") {
            let nodejs_schema = json_object(vec![
                ("type", json_str("object")),
                ("properties", json_object(vec![
                    ("text", json_object(vec![
                        ("type", json_str("string")),
                        ("description", json_str("Text to analyze")),
                    ])),
                ])),
                ("required", json_array(vec![json_str("text")])),
            ]);
            let fib_schema = json_object(vec![
                ("type", json_str("object")),
                ("properties", json_object(vec![
                    ("n", json_object(vec![
                        ("type", json_str("integer")),
                        ("description", json_str("Position in Fibonacci sequence (0-100)")),
                    ])),
                ])),
                ("required", json_array(vec![json_str("n")])),
            ]);
            let pf_schema = json_object(vec![
                ("type", json_str("object")),
                ("properties", json_object(vec![
                    ("n", json_object(vec![
                        ("type", json_str("integer")),
                        ("description", json_str("Number to factor (>= 2)")),
                    ])),
                ])),
                ("required", json_array(vec![json_str("n")])),
            ]);

            let tools = json_array(vec![
                json_object(vec![
                    ("name", json_str("analyze_text")),
                    ("description", json_str("Analyze text: word/char/sentence count, vocabulary richness — Rust MCP server")),
                    ("inputSchema", nodejs_schema),
                ]),
                json_object(vec![
                    ("name", json_str("fibonacci")),
                    ("description", json_str("Calculate nth Fibonacci number — Rust's computational speed")),
                    ("inputSchema", fib_schema),
                ]),
                json_object(vec![
                    ("name", json_str("prime_factors")),
                    ("description", json_str("Calculate prime factors of a number — Rust's math capability")),
                    ("inputSchema", pf_schema),
                ]),
            ]);
            respond(id, &json_object(vec![("tools", tools)]));
        }
        else if line.contains("\"method\":\"tools/call\"") {
            // Parse tool name
            let name = line.split("\"name\":\"")
                .nth(1)
                .and_then(|s| s.split('"').next())
                .unwrap_or("");

            // Find the arguments object
            let args_start = line.find("\"arguments\":");
            let params = match args_start {
                Some(pos) => {
                    let rest = &line[pos + 12..];
                    // Find matching closing brace
                    let mut depth = 0;
                    let mut end = 0;
                    for (i, c) in rest.char_indices() {
                        if c == '{' { depth += 1; }
                        else if c == '}' { depth -= 1; }
                        if depth == 0 { end = i + 1; break; }
                    }
                    &rest[..end]
                }
                None => "{}",
            };

            handle_tool_call(id, name, params);
        }
        else if line.contains("\"method\":\"initialize\"") {
            respond(id, &json_object(vec![
                ("protocolVersion", json_str("0.1.0")),
                ("capabilities", json_object(vec![("tools", "{}".to_string())])),
                ("serverInfo", json_object(vec![
                    ("name", json_str("apex-rust-mcp")),
                    ("version", json_str("1.0.0")),
                ])),
            ]));
        }
        else if line.contains("\"method\":\"server/info\"") {
            respond(id, &json_object(vec![
                ("name", json_str("Rust MCP Server")),
                ("version", json_str("1.0.0")),
                ("language", json_str("rust")),
                ("runtime", json_str("rustc 1.84")),
                ("tools", json_array(vec![
                    json_str("analyze_text"), json_str("fibonacci"), json_str("prime_factors"),
                ])),
            ]));
        }
        else {
            respond_error(id, -32601, &format!("Method not found"));
        }
    }
}
