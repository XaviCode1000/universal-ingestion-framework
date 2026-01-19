---
url: https://geminicli.com/docs/get-started/configuration-v1
title: Gemini CLI configuration
author: null
date: '2025-10-09'
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

**Note on deprecated configuration format**

This document describes the legacy v1 format for the `settings.json`

file. This
format is now deprecated.

For details on the new, recommended format, please see the current Configuration documentation.

Gemini CLI offers several ways to configure its behavior, including environment variables, command-line arguments, and settings files. This document outlines the different configuration methods and available settings.

Configuration is applied in the following order of precedence (lower numbers are overridden by higher numbers):

`.env`

files.Gemini CLI uses JSON settings files for persistent configuration. There are four locations for these files:

`/etc/gemini-cli/system-defaults.json`

(Linux),
`C:\ProgramData\gemini-cli\system-defaults.json`

(Windows) or
`/Library/Application Support/GeminiCli/system-defaults.json`

(macOS). The
path can be overridden using the `GEMINI_CLI_SYSTEM_DEFAULTS_PATH`

environment variable.`~/.gemini/settings.json`

(where `~`

is your home directory).`.gemini/settings.json`

within your project's root directory.`/etc/gemini-cli/settings.json`

(Linux),
`C:\ProgramData\gemini-cli\settings.json`

(Windows) or
`/Library/Application Support/GeminiCli/settings.json`

(macOS). The path can
be overridden using the `GEMINI_CLI_SYSTEM_SETTINGS_PATH`

environment
variable.**Note on environment variables in settings:** String values within your
`settings.json`

files can reference environment variables using either
`$VAR_NAME`

or `${VAR_NAME}`

syntax. These variables will be automatically
resolved when the settings are loaded. For example, if you have an environment
variable `MY_API_TOKEN`

, you could use it in `settings.json`

like this:
`"apiKey": "$MY_API_TOKEN"`

.

Note for Enterprise Users:For guidance on deploying and managing Gemini CLI in a corporate environment, please see the Enterprise Configuration documentation.

`.gemini`

directory in your projectIn addition to a project settings file, a project's `.gemini`

directory can
contain other project-specific files related to Gemini CLI's operation, such as:

`.gemini/sandbox-macos-custom.sb`

, `.gemini/sandbox.Dockerfile`

).`settings.json`

:** contextFileName** (string or array of strings):

`GEMINI.md`

, `AGENTS.md`

). Can be a single filename or a list of accepted
filenames.`GEMINI.md`

`"contextFileName": "AGENTS.md"`

** bugCommand** (object):

`/bug`

command.`"urlTemplate": "https://github.com/google-gemini/gemini-cli/issues/new?template=bug_report.yml&title={title}&info={info}"`

`urlTemplate`

`{title}`

and `{info}`

placeholders.** fileFiltering** (object):

`"respectGitIgnore": true, "enableRecursiveFileSearch": true`

`respectGitIgnore`

`true`

, git-ignored files (like
`node_modules/`

, `dist/`

, `.env`

) are automatically excluded from @
commands and file listing operations.`enableRecursiveFileSearch`

`disableFuzzySearch`

`true`

, disables the fuzzy search
capabilities when searching for files, which can improve performance on
projects with a large number of files.If you are experiencing performance issues with file searching (e.g., with `@`

completions), especially in projects with a very large number of files, here are
a few things you can try in order of recommendation:

**Use .geminiignore:** Create a

`.geminiignore`

file in your project root
to exclude directories that contain a large number of files that you don't
need to reference (e.g., build artifacts, logs, `node_modules`

). Reducing
the total number of files crawled is the most effective way to improve
performance.**Disable fuzzy search:** If ignoring files is not enough, you can disable
fuzzy search by setting `disableFuzzySearch`

to `true`

in your
`settings.json`

file. This will use a simpler, non-fuzzy matching algorithm,
which can be faster.

**Disable recursive file search:** As a last resort, you can disable
recursive file search entirely by setting `enableRecursiveFileSearch`

to
`false`

. This will be the fastest option as it avoids a recursive crawl of
your project. However, it means you will need to type the full path to files
when using `@`

completions.

** coreTools** (array of strings):

`ShellTool`

. For example,
`"coreTools": ["ShellTool(ls -l)"]`

will only allow the `ls -l`

command to
be executed.`"coreTools": ["ReadFileTool", "GlobTool", "ShellTool(ls)"]`

.** allowedTools** (array of strings):

`undefined`

`coreTools`

.`"allowedTools": ["ShellTool(git status)"]`

.** excludeTools** (array of strings):

`excludeTools`

and
`coreTools`

is excluded. You can also specify command-specific restrictions
for tools that support it, like the `ShellTool`

. For example,
`"excludeTools": ["ShellTool(rm -rf)"]`

will block the `rm -rf`

command.`"excludeTools": ["run_shell_command", "findFiles"]`

.`excludeTools`

for
`run_shell_command`

are based on simple string matching and can be easily
bypassed. This feature is `coreTools`

to explicitly select commands that can be executed.** allowMCPServers** (array of strings):

`--allowed-mcp-server-names`

is set.`"allowMCPServers": ["myPythonServer"]`

.`mcpServers`

at the
system settings level such that the user will not be able to configure any
MCP servers of their own. This should not be used as an airtight security
mechanism.** excludeMCPServers** (array of strings):

`excludeMCPServers`

and `allowMCPServers`

is excluded. Note that this will
be ignored if `--allowed-mcp-server-names`

is set.`"excludeMCPServers": ["myNodeServer"]`

.`mcpServers`

at the
system settings level such that the user will not be able to configure any
MCP servers of their own. This should not be used as an airtight security
mechanism.** autoAccept** (boolean):

`true`

, the CLI will bypass the
confirmation prompt for tools deemed safe.`false`

`"autoAccept": true`

** theme** (string):

`"Default"`

`"theme": "GitHub"`

** vimMode** (boolean):

`false`

`"vimMode": true`

** sandbox** (boolean or string):

`true`

, Gemini CLI uses a pre-built
`gemini-cli-sandbox`

Docker image. For more information, see
Sandboxing.`false`

`"sandbox": "docker"`

** toolDiscoveryCommand** (string):

`stdout`

a JSON array of
function declarations.
Tool wrappers are optional.`"toolDiscoveryCommand": "bin/get_tools"`

** toolCallCommand** (string):

`toolDiscoveryCommand`

. The shell command must
meet the following criteria:
`name`

(exactly as in
function declaration)
as first command line argument.`stdin`

, analogous to
`functionCall.args`

.`stdout`

, analogous to
`functionResponse.response.content`

.`"toolCallCommand": "bin/call_tool"`

** mcpServers** (object):

`serverAlias__actualToolName`

) to avoid conflicts. Note
that the system might strip certain schema properties from MCP tool
definitions for compatibility. At least one of `command`

, `url`

, or
`httpUrl`

must be provided. If multiple are specified, the order of
precedence is `httpUrl`

, then `url`

, then `command`

.`<SERVER_NAME>`

`command`

(string, optional): The command to execute to start the MCP
server via standard I/O.`args`

(array of strings, optional): Arguments to pass to the command.`env`

(object, optional): Environment variables to set for the server
process.`cwd`

(string, optional): The working directory in which to start the
server.`url`

(string, optional): The URL of an MCP server that uses Server-Sent
Events (SSE) for communication.`httpUrl`

(string, optional): The URL of an MCP server that uses
streamable HTTP for communication.`headers`

(object, optional): A map of HTTP headers to send with
requests to `url`

or `httpUrl`

.`timeout`

(number, optional): Timeout in milliseconds for requests to
this MCP server.`trust`

(boolean, optional): Trust this server and bypass all tool call
confirmations.`description`

(string, optional): A brief description of the server,
which may be used for display purposes.`includeTools`

(array of strings, optional): List of tool names to
include from this MCP server. When specified, only the tools listed here
will be available from this server (allowlist behavior). If not
specified, all tools from the server are enabled by default.`excludeTools`

(array of strings, optional): List of tool names to
exclude from this MCP server. Tools listed here will not be available to
the model, even if they are exposed by the server. `excludeTools`

takes precedence over `includeTools`

- if a tool is in
both lists, it will be excluded.** checkpointing** (object):

`{"enabled": false}`

`enabled`

`true`

, the `/restore`

command is available.** preferredEditor** (string):

`vscode`

`"preferredEditor": "vscode"`

** telemetry** (object)

`{"enabled": false, "target": "local", "otlpEndpoint": "http://localhost:4317", "logPrompts": true}`

`enabled`

`target`

`local`

and `gcp`

.`otlpEndpoint`

`logPrompts`

** usageStatisticsEnabled** (boolean):

`true`

** hideTips** (boolean):

**Description:** Enables or disables helpful tips in the CLI interface.

**Default:** `false`

**Example:**

** hideBanner** (boolean):

**Description:** Enables or disables the startup banner (ASCII art logo) in
the CLI interface.

**Default:** `false`

**Example:**

** maxSessionTurns** (number):

`-1`

(unlimited)** summarizeToolOutput** (object):

`tokenBudget`

setting.`run_shell_command`

tool is supported.`{}`

(Disabled by default)** excludedProjectEnvVars** (array of strings):

`.env`

files. This prevents project-specific
environment variables (like `DEBUG=true`

) from interfering with gemini-cli
behavior. Variables from `.gemini/.env`

files are never excluded.`["DEBUG", "DEBUG_MODE"]`

** includeDirectories** (array of strings):

`~`

to refer to the user's home
directory. This setting can be combined with the `--include-directories`

command-line flag.`[]`

** loadMemoryFromIncludeDirectories** (boolean):

`/memory refresh`

command. If
set to `true`

, `GEMINI.md`

files should be loaded from all directories that
are added. If set to `false`

, `GEMINI.md`

should only be loaded from the
current directory.`false`

** showLineNumbers** (boolean):

`true`

** accessibility** (object):

`screenReader`

`--screen-reader`

command-line flag, which will take
precedence over the setting.`disableLoadingPhrases`

`{"screenReader": false, "disableLoadingPhrases": false}`

`settings.json`

:The CLI keeps a history of shell commands you run. To avoid conflicts between different projects, this history is stored in a project-specific directory within your user's home folder.

`~/.gemini/tmp/<project_hash>/shell_history`

`<project_hash>`

is a unique identifier generated from your project's root
path.`shell_history`

.`.env`

filesEnvironment variables are a common way to configure applications, especially for sensitive information like API keys or for settings that might change between environments. For authentication setup, see the Authentication documentation which covers all available authentication methods.

The CLI automatically loads environment variables from an `.env`

file. The
loading order is:

`.env`

file in the current working directory.`.env`

file or reaches the project root (identified by a `.git`

folder) or
the home directory.`~/.env`

(in the user's home directory).**Environment variable exclusion:** Some environment variables (like `DEBUG`

and
`DEBUG_MODE`

) are automatically excluded from being loaded from project `.env`

files to prevent interference with gemini-cli behavior. Variables from
`.gemini/.env`

files are never excluded. You can customize this behavior using
the `excludedProjectEnvVars`

setting in your `settings.json`

file.

`GEMINI_API_KEY`

`~/.bashrc`

, `~/.zshrc`

) or an `.env`

file.`GEMINI_MODEL`

`export GEMINI_MODEL="gemini-2.5-flash"`

`GOOGLE_API_KEY`

`export GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"`

.`GOOGLE_CLOUD_PROJECT`

`GOOGLE_CLOUD_PROJECT`

set in your global environment in Cloud
Shell, it will be overridden by this default. To use a different project in
Cloud Shell, you must define `GOOGLE_CLOUD_PROJECT`

in a `.env`

file.`export GOOGLE_CLOUD_PROJECT="YOUR_PROJECT_ID"`

.`GOOGLE_APPLICATION_CREDENTIALS`

`export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/credentials.json"`

`OTLP_GOOGLE_CLOUD_PROJECT`

`export OTLP_GOOGLE_CLOUD_PROJECT="YOUR_PROJECT_ID"`

.`GOOGLE_CLOUD_LOCATION`

`export GOOGLE_CLOUD_LOCATION="YOUR_PROJECT_LOCATION"`

.`GEMINI_SANDBOX`

`sandbox`

setting in `settings.json`

.`true`

, `false`

, `docker`

, `podman`

, or a custom command string.`HTTP_PROXY`

/ `HTTPS_PROXY`

`export HTTPS_PROXY="http://proxy.example.com:8080"`

`SEATBELT_PROFILE`

`sandbox-exec`

) profile on macOS.`permissive-open`

: (Default) Restricts writes to the project folder (and a
few other folders, see
`packages/cli/src/utils/sandbox-macos-permissive-open.sb`

) but allows other
operations.`strict`

: Uses a strict profile that declines operations by default.`<profile_name>`

: Uses a custom profile. To define a custom profile, create
a file named `sandbox-macos-<profile_name>.sb`

in your project's `.gemini/`

directory (e.g., `my-project/.gemini/sandbox-macos-custom.sb`

).`DEBUG`

or `DEBUG_MODE`

`true`

or `1`

to enable verbose debug logging, which can be helpful
for troubleshooting.`.env`

files by default to prevent interference with gemini-cli behavior. Use
`.gemini/.env`

files if you need to set these for gemini-cli specifically.`NO_COLOR`

`CLI_TITLE`

`CODE_ASSIST_ENDPOINT`

Arguments passed directly when running the CLI can override other configurations for that specific session.

** --model <model_name>** (

`-m <model_name>`

`npm start -- --model gemini-1.5-pro-latest`

** --prompt <your_prompt>** (

`-p <your_prompt>`

** --prompt-interactive <your_prompt>** (

`-i <your_prompt>`

`gemini -i "explain this code"`

** --sandbox** (

`-s`

** --sandbox-image**:

** --debug** (

`-d`

** --help** (or

`-h`

** --show-memory-usage**:

** --yolo**:

** --approval-mode <mode>**:

`default`

: Prompt for approval on each tool call (default behavior)`auto_edit`

: Automatically approve edit tools (replace, write_file) while
prompting for others`yolo`

: Automatically approve all tool calls (equivalent to `--yolo`

)`--yolo`

. Use `--approval-mode=yolo`

instead of
`--yolo`

for the new unified approach.`gemini --approval-mode auto_edit`

** --allowed-tools <tool1,tool2,...>**:

`gemini --allowed-tools "ShellTool(git status)"`

** --telemetry**:

** --telemetry-target**:

** --telemetry-otlp-endpoint**:

** --telemetry-otlp-protocol**:

`grpc`

or `http`

). Defaults to `grpc`

.
See telemetry for more information.** --telemetry-log-prompts**:

** --extensions <extension_name ...>** (

`-e <extension_name ...>`

`gemini -e none`

to disable all extensions.`gemini -e my-extension -e my-other-extension`

** --list-extensions** (

`-l`

** --include-directories <dir1,dir2,...>**:

`--include-directories /path/to/project1,/path/to/project2`

or
`--include-directories /path/to/project1 --include-directories /path/to/project2`

** --screen-reader**:

** --version**:

While not strictly configuration for the CLI's *behavior*, context files
(defaulting to `GEMINI.md`

but configurable via the `contextFileName`

setting)
are crucial for configuring the *instructional context* (also referred to as
"memory") provided to the Gemini model. This powerful feature allows you to give
project-specific instructions, coding style guides, or any relevant background
information to the AI, making its responses more tailored and accurate to your
needs. The CLI includes UI elements, such as an indicator in the footer showing
the number of loaded context files, to keep you informed about the active
context.

`GEMINI.md`

)Here's a conceptual example of what a context file at the root of a TypeScript project might contain:

This example demonstrates how you can provide general project context, specific coding conventions, and even notes about particular files or components. The more relevant and precise your context files are, the better the AI can assist you. Project-specific context files are highly encouraged to establish conventions and context.

`GEMINI.md`

) from
several locations. Content from files lower in this list (more specific)
typically overrides or supplements content from files higher up (more
general). The exact concatenation order and final context can be inspected
using the `/memory show`

command. The typical loading order is:
`~/.gemini/<contextFileName>`

(e.g., `~/.gemini/GEMINI.md`

in
your user home directory).`.git`

folder) or your home directory.`node_modules`

, `.git`

, etc.). The breadth of this
search is limited to 200 directories by default, but can be configured
with a `memoryDiscoveryMaxDirs`

field in your `settings.json`

file.`@path/to/file.md`

syntax. For more details,
see the Memory Import Processor documentation.`/memory refresh`

to force a re-scan and reload of all context files
from all configured locations. This updates the AI's instructional context.`/memory show`

to display the combined instructional context currently
loaded, allowing you to verify the hierarchy and content being used by the
AI.`/memory`

command and its sub-commands (`show`

and `refresh`

).By understanding and utilizing these configuration layers and the hierarchical nature of context files, you can effectively manage the AI's memory and tailor the Gemini CLI's responses to your specific needs and projects.

The Gemini CLI can execute potentially unsafe operations (like shell commands and file modifications) within a sandboxed environment to protect your system.

Sandboxing is disabled by default, but you can enable it in a few ways:

`--sandbox`

or `-s`

flag.`GEMINI_SANDBOX`

environment variable.`--yolo`

or `--approval-mode=yolo`

by default.By default, it uses a pre-built `gemini-cli-sandbox`

Docker image.

For project-specific sandboxing needs, you can create a custom Dockerfile at
`.gemini/sandbox.Dockerfile`

in your project's root directory. This Dockerfile
can be based on the base sandbox image:

When `.gemini/sandbox.Dockerfile`

exists, you can use `BUILD_SANDBOX`

environment variable when running Gemini CLI to automatically build the custom
sandbox image:

To help us improve the Gemini CLI, we collect anonymized usage statistics. This data helps us understand how the CLI is used, identify common issues, and prioritize new features.

**What we collect:**

**What we DON'T collect:**

**How to opt out:**

You can opt out of usage statistics collection at any time by setting the
`usageStatisticsEnabled`

property to `false`

in your `settings.json`

file: