---
url: https://geminicli.com/docs/cli/telemetry
title: Observability with OpenTelemetry
author: null
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

Learn how to enable and setup OpenTelemetry for Gemini CLI.

Built on **OpenTelemetry** — the vendor-neutral, industry-standard
observability framework — Gemini CLI's observability system provides:

All telemetry behavior is controlled through your `.gemini/settings.json`

file.
Environment variables can be used to override the settings in the file.

| Setting | Environment Variable | Description | Values | Default |
|---|---|---|---|---|
`enabled` | `GEMINI_TELEMETRY_ENABLED` | Enable or disable telemetry | `true` /`false` | `false` |
`target` | `GEMINI_TELEMETRY_TARGET` | Where to send telemetry data | `"gcp"` /`"local"` | `"local"` |
`otlpEndpoint` | `GEMINI_TELEMETRY_OTLP_ENDPOINT` | OTLP collector endpoint | URL string | `http://localhost:4317` |
`otlpProtocol` | `GEMINI_TELEMETRY_OTLP_PROTOCOL` | OTLP transport protocol | `"grpc"` /`"http"` | `"grpc"` |
`outfile` | `GEMINI_TELEMETRY_OUTFILE` | Save telemetry to file (overrides `otlpEndpoint` ) | file path | - |
`logPrompts` | `GEMINI_TELEMETRY_LOG_PROMPTS` | Include prompts in telemetry logs | `true` /`false` | `true` |
`useCollector` | `GEMINI_TELEMETRY_USE_COLLECTOR` | Use external OTLP collector (advanced) | `true` /`false` | `false` |
`useCliAuth` | `GEMINI_TELEMETRY_USE_CLI_AUTH` | Use CLI credentials for telemetry (GCP target only) | `true` /`false` | `false` |

**Note on boolean environment variables:** For the boolean settings (`enabled`

,
`logPrompts`

, `useCollector`

), setting the corresponding environment variable to
`true`

or `1`

will enable the feature. Any other value will disable it.

For detailed information about all configuration options, see the Configuration guide.

Before using either method below, complete these steps:

Set your Google Cloud project ID:

Authenticate with Google Cloud:

Make sure your account or service account has these IAM roles:

Enable the required Google Cloud APIs (if not already enabled):

By default, the telemetry collector for Google Cloud uses Application Default Credentials (ADC). However, you can configure it to use the same OAuth credentials that you use to log in to the Gemini CLI. This is useful in environments where you don't have ADC set up.

To enable this, set the `useCliAuth`

property in your `telemetry`

settings to
`true`

:

**Important:**

`useCollector: true`

. If you enable both, telemetry
will be disabled and an error will be logged.Sends telemetry directly to Google Cloud services. No collector needed.

`.gemini/settings.json`

:
For custom processing, filtering, or routing, use an OpenTelemetry collector to forward data to Google Cloud.

`.gemini/settings.json`

:
`~/.gemini/tmp/<projectHash>/otel/collector-gcp.log`

`Ctrl+C`

)`~/.gemini/tmp/<projectHash>/otel/collector-gcp.log`

to view local
collector logs.Gemini CLI provides a pre-configured Google Cloud Monitoring dashboard to visualize your telemetry.

This dashboard can be found under **Google Cloud Monitoring Dashboard
Templates** as "**Gemini CLI Monitoring**".

To learn more, check out this blog post: Instant insights: Gemini CLI's new pre-configured monitoring dashboards.

For local development and debugging, you can capture telemetry data locally:

`.gemini/settings.json`

:
`.gemini/telemetry.log`

).`~/.gemini/tmp/<projectHash>/otel/collector.log`

`Ctrl+C`

)The following section describes the structure of logs and metrics generated for Gemini CLI.

The `session.id`

, `installation.id`

, and `user.email`

(available only when
authenticated with a Google account) are included as common attributes on all
logs and metrics.

Logs are timestamped records of specific events. The following events are logged for Gemini CLI, grouped by category.

Captures startup configuration and user prompt submissions.

`gemini_cli.config`

: Emitted once at startup with the CLI configuration.

`model`

(string)`embedding_model`

(string)`sandbox_enabled`

(boolean)`core_tools_enabled`

(string)`approval_mode`

(string)`api_key_enabled`

(boolean)`vertex_ai_enabled`

(boolean)`log_user_prompts_enabled`

(boolean)`file_filtering_respect_git_ignore`

(boolean)`debug_mode`

(boolean)`mcp_servers`

(string)`mcp_servers_count`

(int)`extensions`

(string)`extension_ids`

(string)`extension_count`

(int)`mcp_tools`

(string, if applicable)`mcp_tools_count`

(int, if applicable)`output_format`

("text", "json", or "stream-json")`gemini_cli.user_prompt`

: Emitted when a user submits a prompt.

`prompt_length`

(int)`prompt_id`

(string)`prompt`

(string; excluded if `telemetry.logPrompts`

is `false`

)`auth_type`

(string)Captures tool executions, output truncation, and Edit behavior.

`gemini_cli.tool_call`

: Emitted for each tool (function) call.

`function_name`

`function_args`

`duration_ms`

`success`

(boolean)`decision`

("accept", "reject", "auto_accept", or "modify", if applicable)`error`

(if applicable)`error_type`

(if applicable)`prompt_id`

(string)`tool_type`

("native" or "mcp")`mcp_server_name`

(string, if applicable)`extension_name`

(string, if applicable)`extension_id`

(string, if applicable)`content_length`

(int, if applicable)`metadata`

(if applicable)`gemini_cli.tool_output_truncated`

: Output of a tool call was truncated.

`tool_name`

(string)`original_content_length`

(int)`truncated_content_length`

(int)`threshold`

(int)`lines`

(int)`prompt_id`

(string)`gemini_cli.edit_strategy`

: Edit strategy chosen.

`strategy`

(string)`gemini_cli.edit_correction`

: Edit correction result.

`correction`

("success" | "failure")`gen_ai.client.inference.operation.details`

: This event provides detailed
information about the GenAI operation, aligned with OpenTelemetry GenAI
semantic conventions for events.

`gen_ai.request.model`

(string)`gen_ai.provider.name`

(string)`gen_ai.operation.name`

(string)`gen_ai.input.messages`

(json string)`gen_ai.output.messages`

(json string)`gen_ai.response.finish_reasons`

(array of strings)`gen_ai.usage.input_tokens`

(int)`gen_ai.usage.output_tokens`

(int)`gen_ai.request.temperature`

(float)`gen_ai.request.top_p`

(float)`gen_ai.request.top_k`

(int)`gen_ai.request.max_tokens`

(int)`gen_ai.system_instructions`

(json string)`server.address`

(string)`server.port`

(int)Tracks file operations performed by tools.

`gemini_cli.file_operation`

: Emitted for each file operation.
`tool_name`

(string)`operation`

("create" | "read" | "update")`lines`

(int, optional)`mimetype`

(string, optional)`extension`

(string, optional)`programming_language`

(string, optional)Captures Gemini API requests, responses, and errors.

`gemini_cli.api_request`

: Request sent to Gemini API.

`model`

(string)`prompt_id`

(string)`request_text`

(string, optional)`gemini_cli.api_response`

: Response received from Gemini API.

`model`

(string)`status_code`

(int|string)`duration_ms`

(int)`input_token_count`

(int)`output_token_count`

(int)`cached_content_token_count`

(int)`thoughts_token_count`

(int)`tool_token_count`

(int)`total_token_count`

(int)`response_text`

(string, optional)`prompt_id`

(string)`auth_type`

(string)`finish_reasons`

(array of strings)`gemini_cli.api_error`

: API request failed.

`model`

(string)`error`

(string)`error_type`

(string)`status_code`

(int|string)`duration_ms`

(int)`prompt_id`

(string)`auth_type`

(string)`gemini_cli.malformed_json_response`

: `generateJson`

response could not be
parsed.

`model`

(string)`gemini_cli.slash_command`

: A slash command was executed.

`command`

(string)`subcommand`

(string, optional)`status`

("success" | "error")`gemini_cli.slash_command.model`

: Model was selected via slash command.

`model_name`

(string)`gemini_cli.model_routing`

: Model router made a decision.

`decision_model`

(string)`decision_source`

(string)`routing_latency_ms`

(int)`reasoning`

(string, optional)`failed`

(boolean)`error_message`

(string, optional)`gemini_cli.chat_compression`

: Chat context was compressed.

`tokens_before`

(int)`tokens_after`

(int)`gemini_cli.chat.invalid_chunk`

: Invalid chunk received from a stream.

`error.message`

(string, optional)`gemini_cli.chat.content_retry`

: Retry triggered due to a content error.

`attempt_number`

(int)`error_type`

(string)`retry_delay_ms`

(int)`model`

(string)`gemini_cli.chat.content_retry_failure`

: All content retries failed.

`total_attempts`

(int)`final_error_type`

(string)`total_duration_ms`

(int, optional)`model`

(string)`gemini_cli.conversation_finished`

: Conversation session ended.

`approvalMode`

(string)`turnCount`

(int)`gemini_cli.next_speaker_check`

: Next speaker determination.

`prompt_id`

(string)`finish_reason`

(string)`result`

(string)Records fallback mechanisms for models and network operations.

`gemini_cli.flash_fallback`

: Switched to a flash model as fallback.

`auth_type`

(string)`gemini_cli.ripgrep_fallback`

: Switched to grep as fallback for file search.

`error`

(string, optional)`gemini_cli.web_fetch_fallback_attempt`

: Attempted web-fetch fallback.

`reason`

("private_ip" | "primary_failed")Tracks extension lifecycle and settings changes.

`gemini_cli.extension_install`

: An extension was installed.

`extension_name`

(string)`extension_version`

(string)`extension_source`

(string)`status`

(string)`gemini_cli.extension_uninstall`

: An extension was uninstalled.

`extension_name`

(string)`status`

(string)`gemini_cli.extension_enable`

: An extension was enabled.

`extension_name`

(string)`setting_scope`

(string)`gemini_cli.extension_disable`

: An extension was disabled.

`extension_name`

(string)`setting_scope`

(string)`gemini_cli.extension_update`

: An extension was updated.

`extension_name`

(string)`extension_version`

(string)`extension_previous_version`

(string)`extension_source`

(string)`status`

(string)`gemini_cli.agent.start`

: Agent run started.

`agent_id`

(string)`agent_name`

(string)`gemini_cli.agent.finish`

: Agent run finished.

`agent_id`

(string)`agent_name`

(string)`duration_ms`

(int)`turn_count`

(int)`terminate_reason`

(string)Captures IDE connectivity and conversation lifecycle events.

`gemini_cli.ide_connection`

: IDE companion connection.
`connection_type`

(string)Tracks terminal rendering issues and related signals.

`kitty_sequence_overflow`

: Terminal kitty control sequence overflow.
`sequence_length`

(int)`truncated_sequence`

(string)Metrics are numerical measurements of behavior over time.

Counts CLI sessions at startup.

`gemini_cli.session.count`

(Counter, Int): Incremented once per CLI startup.Measures tool usage and latency.

`gemini_cli.tool.call.count`

(Counter, Int): Counts tool calls.

`function_name`

`success`

(boolean)`decision`

(string: "accept", "reject", "modify", or "auto_accept", if
applicable)`tool_type`

(string: "mcp" or "native", if applicable)`gemini_cli.tool.call.latency`

(Histogram, ms): Measures tool call latency.

`function_name`

Tracks API request volume and latency.

`gemini_cli.api.request.count`

(Counter, Int): Counts all API requests.

`model`

`status_code`

`error_type`

(if applicable)`gemini_cli.api.request.latency`

(Histogram, ms): Measures API request
latency.

`model`

`gen_ai.client.operation.duration`

(GenAI conventions).Tracks tokens used by model and type.

`gemini_cli.token.usage`

(Counter, Int): Counts tokens used.
`model`

`type`

("input", "output", "thought", "cache", or "tool")`gen_ai.client.token.usage`

for `input`

/`output`

.Counts file operations with basic context.

`gemini_cli.file.operation.count`

(Counter, Int): Counts file operations.

`operation`

("create", "read", "update")`lines`

(Int, optional)`mimetype`

(string, optional)`extension`

(string, optional)`programming_language`

(string, optional)`gemini_cli.lines.changed`

(Counter, Int): Number of lines changed (from file
diffs).

`function_name`

`type`

("added" or "removed")Resilience counters for compression, invalid chunks, and retries.

`gemini_cli.chat_compression`

(Counter, Int): Counts chat compression
operations.

`tokens_before`

(Int)`tokens_after`

(Int)`gemini_cli.chat.invalid_chunk.count`

(Counter, Int): Counts invalid chunks
from streams.

`gemini_cli.chat.content_retry.count`

(Counter, Int): Counts retries due to
content errors.

`gemini_cli.chat.content_retry_failure.count`

(Counter, Int): Counts requests
where all content retries failed.

Routing latency/failures and slash-command selections.

`gemini_cli.slash_command.model.call_count`

(Counter, Int): Counts model
selections via slash command.

`slash_command.model.model_name`

(string)`gemini_cli.model_routing.latency`

(Histogram, ms): Model routing decision
latency.

`routing.decision_model`

(string)`routing.decision_source`

(string)`gemini_cli.model_routing.failure.count`

(Counter, Int): Counts model routing
failures.

`routing.decision_source`

(string)`routing.error_message`

(string)Agent lifecycle metrics: runs, durations, and turns.

`gemini_cli.agent.run.count`

(Counter, Int): Counts agent runs.

`agent_name`

(string)`terminate_reason`

(string)`gemini_cli.agent.duration`

(Histogram, ms): Agent run durations.

`agent_name`

(string)`gemini_cli.agent.turns`

(Histogram, turns): Turns taken per agent run.

`agent_name`

(string)UI stability signals such as flicker count.

`gemini_cli.ui.flicker.count`

(Counter, Int): Counts UI frames that flicker
(render taller than terminal).Optional performance monitoring for startup, CPU/memory, and phase timing.

`gemini_cli.startup.duration`

(Histogram, ms): CLI startup time by phase.

`phase`

(string)`details`

(map, optional)`gemini_cli.memory.usage`

(Histogram, bytes): Memory usage.

`memory_type`

("heap_used", "heap_total", "external", "rss")`component`

(string, optional)`gemini_cli.cpu.usage`

(Histogram, percent): CPU usage percentage.

`component`

(string, optional)`gemini_cli.tool.queue.depth`

(Histogram, count): Number of tools in the
execution queue.

`gemini_cli.tool.execution.breakdown`

(Histogram, ms): Tool time by phase.

`function_name`

(string)`phase`

("validation", "preparation", "execution", "result_processing")`gemini_cli.api.request.breakdown`

(Histogram, ms): API request time by phase.

`model`

(string)`phase`

("request_preparation", "network_latency", "response_processing",
"token_processing")`gemini_cli.token.efficiency`

(Histogram, ratio): Token efficiency metrics.

`model`

(string)`metric`

(string)`context`

(string, optional)`gemini_cli.performance.score`

(Histogram, score): Composite performance
score.

`category`

(string)`baseline`

(number, optional)`gemini_cli.performance.regression`

(Counter, Int): Regression detection
events.

`metric`

(string)`severity`

("low", "medium", "high")`current_value`

(number)`baseline_value`

(number)`gemini_cli.performance.regression.percentage_change`

(Histogram, percent):
Percent change from baseline when regression detected.

`metric`

(string)`severity`

("low", "medium", "high")`current_value`

(number)`baseline_value`

(number)`gemini_cli.performance.baseline.comparison`

(Histogram, percent): Comparison
to baseline.

`metric`

(string)`category`

(string)`current_value`

(number)`baseline_value`

(number)The following metrics comply with OpenTelemetry GenAI semantic conventions for standardized observability across GenAI applications:

`gen_ai.client.token.usage`

(Histogram, token): Number of input and output
tokens used per operation.

`gen_ai.operation.name`

(string): The operation type (e.g.,
"generate_content", "chat")`gen_ai.provider.name`

(string): The GenAI provider ("gcp.gen_ai" or
"gcp.vertex_ai")`gen_ai.token.type`

(string): The token type ("input" or "output")`gen_ai.request.model`

(string, optional): The model name used for the
request`gen_ai.response.model`

(string, optional): The model name that generated
the response`server.address`

(string, optional): GenAI server address`server.port`

(int, optional): GenAI server port`gen_ai.client.operation.duration`

(Histogram, s): GenAI operation duration in
seconds.

`gen_ai.operation.name`

(string): The operation type (e.g.,
"generate_content", "chat")`gen_ai.provider.name`

(string): The GenAI provider ("gcp.gen_ai" or
"gcp.vertex_ai")`gen_ai.request.model`

(string, optional): The model name used for the
request`gen_ai.response.model`

(string, optional): The model name that generated
the response`server.address`

(string, optional): GenAI server address`server.port`

(int, optional): GenAI server port`error.type`

(string, optional): Error type if the operation failed