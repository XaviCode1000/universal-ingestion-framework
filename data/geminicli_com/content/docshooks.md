---
url: https://geminicli.com/docs/hooks
title: Gemini CLI hooks
author: null
date: '2025-12-01'
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

Hooks are scripts or programs that Gemini CLI executes at specific points in the agentic loop, allowing you to intercept and customize behavior without modifying the CLI's source code.

Note: Hooks are currently an experimental feature.To use hooks, you must explicitly enable them in your

`settings.json`

:Both of these are needed in this experimental phase.

See writing hooks guide for a tutorial on creating your first hook and a comprehensive example.

See hooks reference for the technical specification of the I/O schemas.

See best practices for guidelines on security, performance, and debugging.

With hooks, you can:

Hooks run synchronously as part of the agent loop—when a hook event fires, Gemini CLI waits for all matching hooks to complete before continuing.

Warning: Hooks execute arbitrary code with your user privileges.By configuring hooks, you are explicitly allowing Gemini CLI to run shell commands on your machine. Malicious or poorly configured hooks can:

`.env`

, ssh keys) and send them to
remote servers.**Project-level hooks** (in `.gemini/settings.json`

) and **Extension hooks** are
particularly risky when opening third-party projects or extensions from
untrusted authors. Gemini CLI will **warn you** the first time it detects a new
project hook (identified by its name and command), but it is **your
responsibility** to review these hooks (and any installed extensions) before
trusting them.

Note:Extension hooks are subject to a mandatory security warning and consent flow during extension installation or update if hooks are detected. You must explicitly approve the installation or update of any extension that contains hooks.

See Security Considerations for a detailed threat model and mitigation strategies.

Hooks are triggered by specific events in Gemini CLI's lifecycle. The following table lists all available hook events:

| Event | When It Fires | Common Use Cases |
|---|---|---|
`SessionStart` | When a session begins | Initialize resources, load context |
`SessionEnd` | When a session ends | Clean up, save state |
`BeforeAgent` | After user submits prompt, before planning | Add context, validate prompts |
`AfterAgent` | When agent loop ends | Review output, force continuation |
`BeforeModel` | Before sending request to LLM | Modify prompts, add instructions |
`AfterModel` | After receiving LLM response | Filter responses, log interactions |
`BeforeToolSelection` | Before LLM selects tools (after BeforeModel) | Filter available tools, optimize selection |
`BeforeTool` | Before a tool executes | Validate arguments, block dangerous ops |
`AfterTool` | After a tool executes | Process results, run tests |
`PreCompress` | Before context compression | Save state, notify user |
`Notification` | When a notification occurs (e.g., permission) | Auto-approve, log decisions |

Gemini CLI currently supports **command hooks** that run shell commands or
scripts:

**Note:** Plugin hooks (npm packages) are planned for a future release.

For tool-related events (`BeforeTool`

, `AfterTool`

), you can filter which tools
trigger the hook:

**Matcher patterns:**

`"read_file"`

matches only `read_file`

`"write_.*|replace"`

matches `write_file`

, `replace`

`"*"`

or `""`

matches all tools**Session event matchers:**

`startup`

, `resume`

, `clear`

`exit`

, `clear`

, `logout`

, `prompt_input_exit`

`manual`

, `auto`

`ToolPermission`

Hooks communicate via:

Every hook receives these base fields:

**Input:**

**Output (JSON on stdout):**

Or simple exit codes:

**Input:**

**Output:**

**Input:**

**Output:**

**Input:**

**Output:**

**Input:**

**Output:**

**Input:**

**Output:**

Or simple output (comma-separated tool names sets mode to ANY):

**Input:**

**Output:**

**Input:**

No structured output expected (but stdout/stderr logged).

**Input:**

**Output:**

**Input:**

**Output:**

Hook definitions are configured in `settings.json`

files using the `hooks`

object. Configuration can be specified at multiple levels with defined
precedence rules.

Hook configurations are applied in the following order of execution (lower numbers run first):

`.gemini/settings.json`

in your project directory
(highest priority)`~/.gemini/settings.json`

`/etc/gemini-cli/settings.json`

If multiple hooks with the identical **name** and **command** are discovered
across different configuration layers, Gemini CLI deduplicates them. The hook
from the higher-priority layer (e.g., Project) will be kept, and others will be
ignored.

Within each level, hooks run in the order they are declared in the configuration.

**Configuration properties:**

`name`

`/hooks enable/disable`

commands. If omitted, the `command`

path is used as
the identifier.`type`

`"command"`

is
supported`command`

`description`

`/hooks panel`

`timeout`

`matcher`

Hooks have access to:

`GEMINI_PROJECT_DIR`

: Project root directory`GEMINI_SESSION_ID`

: Current session ID`GEMINI_API_KEY`

: Gemini API key (if configured)Use the `/hooks panel`

command to view all registered hooks:

This command displays:

You can enable or disable all hooks at once using commands:

These commands provide a shortcut to enable or disable all configured hooks
without managing them individually. The `enable-all`

command removes all hooks
from the `hooks.disabled`

array, while `disable-all`

adds all configured hooks
to the disabled list. Changes take effect immediately without requiring a
restart.

You can enable or disable individual hooks using commands:

These commands allow you to control hook execution without editing configuration
files. The hook name should match the `name`

field in your hook configuration.
Changes made via these commands are persisted to your settings. The settings are
saved to workspace scope if available, otherwise to your global user settings
(`~/.gemini/settings.json`

).

To permanently disable hooks, add them to the `hooks.disabled`

array in your
`settings.json`

:

**Note:** The `hooks.disabled`

array uses a UNION merge strategy. Disabled hooks
from all configuration levels (user, project, system) are combined and
deduplicated, meaning a hook disabled at any level remains disabled.

If you have hooks configured for Claude Code, you can migrate them:

This command:

`.claude/settings.json`

`PreToolUse`

→ `BeforeTool`

, etc.)`Bash`

→ `run_shell_command`

, `replace`

→ `replace`

)`.gemini/settings.json`

| Claude Code | Gemini CLI |
|---|---|
`PreToolUse` | `BeforeTool` |
`PostToolUse` | `AfterTool` |
`UserPromptSubmit` | `BeforeAgent` |
`Stop` | `AfterAgent` |
`Notification` | `Notification` |
`SessionStart` | `SessionStart` |
`SessionEnd` | `SessionEnd` |
`PreCompact` | `PreCompress` |

| Claude Code | Gemini CLI |
|---|---|
`Bash` | `run_shell_command` |
`Edit` | `replace` |
`Read` | `read_file` |
`Write` | `write_file` |
`Glob` | `glob` |
`Grep` | `search_file_content` |
`LS` | `list_directory` |

The following built-in tools can be used in `BeforeTool`

and `AfterTool`

hook
matchers:

`read_file`

- Read a single file`read_many_files`

- Read multiple files at once`write_file`

- Create or overwrite a file`replace`

- Edit file content with find/replace`list_directory`

- List directory contents`glob`

- Find files matching a pattern`search_file_content`

- Search within file contents`run_shell_command`

- Execute shell commands`google_web_search`

- Google Search with grounding`web_fetch`

- Fetch web page content`write_todos`

- Manage TODO items`save_memory`

- Save information to memory`delegate_to_agent`

- Delegate tasks to sub-agents`startup`

- Fresh session start`resume`

- Resuming a previous session`clear`

- Session cleared`exit`

- Normal exit`clear`

- Session cleared`logout`

- User logged out`prompt_input_exit`

- Exit from prompt input`other`

- Other reasons`manual`

- Manually triggered compression`auto`

- Automatically triggered compression`ToolPermission`

- Tool permission notifications