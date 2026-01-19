---
url: https://geminicli.com/docs/cli/headless
title: Headless mode
author: null
date: '2025-10-10'
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

Headless mode allows you to run Gemini CLI programmatically from command line
scripts and automation tools without any interactive UI. This is ideal for
scripting, automation, CI/CD pipelines, and building AI-powered tools.

The headless mode provides a headless interface to Gemini CLI that:

Accepts prompts via command line arguments or stdin
Returns structured output (text or JSON)
Supports file redirection and piping
Enables automation and scripting workflows
Provides consistent exit codes for error handling
Use the `--prompt`

(or `-p`

) flag to run in headless mode:

Terminal window gemini --prompt "What is machine learning?"

Pipe input to Gemini CLI from your terminal:

Terminal window echo "Explain this code" | gemini

Read from files and process with Gemini:

Terminal window cat README.md | gemini --prompt "Summarize this documentation"

Standard human-readable output:

Terminal window gemini -p "What is the capital of France?"

Response format:

The capital of France is Paris.

Returns structured data including response, statistics, and metadata. This
format is ideal for programmatic processing and automation scripts.

The JSON output follows this high-level structure:

"response" : "string" , // The main AI-generated content answering your prompt

// Usage metrics and performance data

// Per-model API and token usage statistics

/* request counts, errors, latency */

/* prompt, response, cached, total counts */

// Tool execution statistics

"totalSuccess" : "number" ,

"totalDurationMs" : "number" ,

/* accept, reject, modify, auto_accept counts */

/* per-tool detailed stats */

// File modification statistics

"totalLinesAdded" : "number" ,

"totalLinesRemoved" : "number"

// Present only when an error occurred

"type" : "string" , // Error type (e.g., "ApiError", "AuthError")

"message" : "string" , // Human-readable error description

"code" : "number" // Optional error code

Terminal window gemini -p "What is the capital of France?" --output-format json

Response:

"response" : "The capital of France is Paris." ,

Returns real-time events as newline-delimited JSON (JSONL). Each significant
action (initialization, messages, tool calls, results) emits immediately as it
occurs. This format is ideal for monitoring long-running operations, building
UIs with live progress, and creating automation pipelines that react to events.

Use `--output-format stream-json`

when you need:

Real-time progress monitoring - See tool calls and responses as they
happen
Event-driven automation - React to specific events (e.g., tool failures)
Live UI updates - Build interfaces showing AI agent activity in real-time
Detailed execution logs - Capture complete interaction history with
timestamps
Pipeline integration - Stream events to logging/monitoring systems
The streaming format emits 6 event types:

`init`

- Session starts (includes session_id, model)
`message`

- User prompts and assistant responses
`tool_use`

- Tool call requests with parameters
`tool_result`

- Tool execution results (success/error)
`error`

- Non-fatal errors and warnings
`result`

- Final session outcome with aggregated stats
Terminal window # Stream events to console

gemini --output-format stream-json --prompt "What is 2+2?"

# Save event stream to file

gemini --output-format stream-json --prompt "Analyze this code" > events.jsonl

gemini --output-format stream-json --prompt "List files" | jq -r '.type'

Each line is a complete JSON event:

{ "type" : "init" , "timestamp" : "2025-10-10T12:00:00.000Z" , "session_id" : "abc123" , "model" : "gemini-2.0-flash-exp" }

{ "type" : "message" , "role" : "user" , "content" : "List files in current directory" , "timestamp" : "2025-10-10T12:00:01.000Z" }

{ "type" : "tool_use" , "tool_name" : "Bash" , "tool_id" : "bash-123" , "parameters" :{ "command" : "ls -la" }, "timestamp" : "2025-10-10T12:00:02.000Z" }

{ "type" : "tool_result" , "tool_id" : "bash-123" , "status" : "success" , "output" : "file1.txt \n file2.txt" , "timestamp" : "2025-10-10T12:00:03.000Z" }

{ "type" : "message" , "role" : "assistant" , "content" : "Here are the files..." , "delta" : true , "timestamp" : "2025-10-10T12:00:04.000Z" }

{ "type" : "result" , "status" : "success" , "stats" :{ "total_tokens" : 250 , "input_tokens" : 50 , "output_tokens" : 200 , "duration_ms" : 3000 , "tool_calls" : 1 }, "timestamp" : "2025-10-10T12:00:05.000Z" }

Save output to files or pipe to other commands:

Terminal window gemini -p "Explain Docker" > docker-explanation.txt

gemini -p "Explain Docker" --output-format json > docker-explanation.json

gemini -p "Add more details" >> docker-explanation.txt

gemini -p "What is Kubernetes?" --output-format json | jq '.response'

gemini -p "Explain microservices" | wc -w

gemini -p "List programming languages" | grep -i "python"

Key command-line options for headless usage:

Option Description Example `--prompt`

, `-p`

Run in headless mode `gemini -p "query"`

`--output-format`

Specify output format (text, json) `gemini -p "query" --output-format json`

`--model`

, `-m`

Specify the Gemini model `gemini -p "query" -m gemini-2.5-flash`

`--debug`

, `-d`

Enable debug mode `gemini -p "query" --debug`

`--include-directories`

Include additional directories `gemini -p "query" --include-directories src,docs`

`--yolo`

, `-y`

Auto-approve all actions `gemini -p "query" --yolo`

`--approval-mode`

Set approval mode `gemini -p "query" --approval-mode auto_edit`

For complete details on all available configuration options, settings files, and
environment variables, see the
Configuration Guide .

Terminal window cat src/auth.py | gemini -p "Review this authentication code for security issues" > security-review.txt

Terminal window result = $( git diff --cached | gemini -p "Write a concise commit message for these changes" --output-format json )

echo " $result " | jq -r '.response'

Terminal window result = $( cat api/routes.js | gemini -p "Generate OpenAPI spec for these routes" --output-format json )

echo " $result " | jq -r '.response' > openapi.json

Terminal window echo "Analyzing $file ..."

result = $( cat " $file " | gemini -p "Find potential bugs and suggest improvements" --output-format json )

echo " $result " | jq -r '.response' > "reports/$( basename " $file ").analysis"

echo "Completed analysis for $( basename " $file ")" >> reports/progress.log

Terminal window result = $( git diff origin/main...HEAD | gemini -p "Review these changes for bugs, security issues, and code quality" --output-format json )

echo " $result " | jq -r '.response' > pr-review.json

Terminal window grep "ERROR" /var/log/app.log | tail -20 | gemini -p "Analyze these errors and suggest root cause and fixes" > error-analysis.txt

Terminal window result = $( git log --oneline v1.0.0..HEAD | gemini -p "Generate release notes from these commits" --output-format json )

response = $( echo " $result " | jq -r '.response' )

echo " $response " >> CHANGELOG.md

Terminal window result = $( gemini -p "Explain this database schema" --include-directories db --output-format json )

total_tokens = $( echo " $result " | jq -r '.stats.models // {} | to_entries | map(.value.tokens.total) | add // 0' )

models_used = $( echo " $result " | jq -r '.stats.models // {} | keys | join(", ") | if . == "" then "none" else . end' )

tool_calls = $( echo " $result " | jq -r '.stats.tools.totalCalls // 0' )

tools_used = $( echo " $result " | jq -r '.stats.tools.byName // {} | keys | join(", ") | if . == "" then "none" else . end' )

echo "$( date ): $total_tokens tokens, $tool_calls tool calls ( $tools_used ) used with models: $models_used " >> usage.log

echo " $result " | jq -r '.response' > schema-docs.md

echo "Recent usage trends:"