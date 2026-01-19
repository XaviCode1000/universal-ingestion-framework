---
url: https://geminicli.com/docs/get-started/configuration
title: Gemini CLI configuration
author: null
date: '2025-10-09'
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

Gemini CLI offers several ways to configure its behavior, including environment
variables, command-line arguments, and settings files. This document outlines
the different configuration methods and available settings.

Gemini CLI uses JSON settings files for persistent configuration. There are four
locations for these files:

Tip: JSON-aware editors can use autocomplete and validation by pointing to
the generated schema at schemas/settings.schema.json in this repository.
When working outside the repo, reference the hosted schema at
https://raw.githubusercontent.com/google-gemini/gemini-cli/main/schemas/settings.schema.json.

System defaults file:

Location:/etc/gemini-cli/system-defaults.json (Linux),
C:\ProgramData\gemini-cli\system-defaults.json (Windows) or
/Library/Application Support/GeminiCli/system-defaults.json (macOS). The
path can be overridden using the GEMINI_CLI_SYSTEM_DEFAULTS_PATH
environment variable.

Scope: Provides a base layer of system-wide default settings. These
settings have the lowest precedence and are intended to be overridden by
user, project, or system override settings.

User settings file:

Location:~/.gemini/settings.json (where ~ is your home directory).

Scope: Applies to all Gemini CLI sessions for the current user. User
settings override system defaults.

Project settings file:

Location:.gemini/settings.json within your project's root directory.

Scope: Applies only when running Gemini CLI from that specific project.
Project settings override user settings and system defaults.

System settings file:

Location:/etc/gemini-cli/settings.json (Linux),
C:\ProgramData\gemini-cli\settings.json (Windows) or
/Library/Application Support/GeminiCli/settings.json (macOS). The path can
be overridden using the GEMINI_CLI_SYSTEM_SETTINGS_PATH environment
variable.

Scope: Applies to all Gemini CLI sessions on the system, for all users.
System settings act as overrides, taking precedence over all other settings
files. May be useful for system administrators at enterprises to have
controls over users' Gemini CLI setups.

Note on environment variables in settings: String values within your
settings.json and gemini-extension.json files can reference environment
variables using either $VAR_NAME or ${VAR_NAME} syntax. These variables will
be automatically resolved when the settings are loaded. For example, if you have
an environment variable MY_API_TOKEN, you could use it in settings.json like
this: "apiKey": "$MY_API_TOKEN". Additionally, each extension can have its own
.env file in its directory, which will be loaded automatically.

Note for Enterprise Users: For guidance on deploying and managing Gemini
CLI in a corporate environment, please see the
Enterprise Configuration documentation.

In addition to a project settings file, a project's .gemini directory can
contain other project-specific files related to Gemini CLI's operation, such as:

Description: The color theme for the UI. See the CLI themes guide for
available options.

Default:undefined

ui.customThemes (object):

Description: Custom theme definitions.

Default:{}

ui.hideWindowTitle (boolean):

Description: Hide the window title bar

Default:false

Requires restart: Yes

ui.showStatusInTitle (boolean):

Description: Show Gemini CLI model thoughts in the terminal window title
during the working phase

Default:false

ui.dynamicWindowTitle (boolean):

Description: Update the terminal window title with current status icons
(Ready: ◇, Action Required: ✋, Working: ✦)

Default:true

ui.showHomeDirectoryWarning (boolean):

Description: Show a warning when running Gemini CLI in the home
directory.

Default:true

Requires restart: Yes

ui.hideTips (boolean):

Description: Hide helpful tips in the UI

Default:false

ui.hideBanner (boolean):

Description: Hide the application banner

Default:false

ui.hideContextSummary (boolean):

Description: Hide the context summary (GEMINI.md, MCP servers) above the
input.

Default:false

ui.footer.hideCWD (boolean):

Description: Hide the current working directory path in the footer.

Default:false

ui.footer.hideSandboxStatus (boolean):

Description: Hide the sandbox status indicator in the footer.

Default:false

ui.footer.hideModelInfo (boolean):

Description: Hide the model name and context usage in the footer.

Default:false

ui.footer.hideContextPercentage (boolean):

Description: Hides the context window remaining percentage.

Default:true

ui.hideFooter (boolean):

Description: Hide the footer from the UI

Default:false

ui.showMemoryUsage (boolean):

Description: Display memory usage information in the UI

Default:false

ui.showLineNumbers (boolean):

Description: Show line numbers in the chat.

Default:true

ui.showCitations (boolean):

Description: Show citations for generated text in the chat.

Default:false

ui.showModelInfoInChat (boolean):

Description: Show the model name in the chat for each model turn.

Default:false

ui.useFullWidth (boolean):

Description: Use the entire width of the terminal for output.

Default:true

ui.useAlternateBuffer (boolean):

Description: Use an alternate screen buffer for the UI, preserving shell
history.

Default:false

Requires restart: Yes

ui.incrementalRendering (boolean):

Description: Enable incremental rendering for the UI. This option will
reduce flickering but may cause rendering artifacts. Only supported when
useAlternateBuffer is enabled.

Default:true

Requires restart: Yes

ui.customWittyPhrases (array):

Description: Custom witty phrases to display during loading. When
provided, the CLI cycles through these instead of the defaults.

Default:[]

ui.accessibility.enableLoadingPhrases (boolean):

Description: Enable loading phrases during operations.

Default:true

Requires restart: Yes

ui.accessibility.screenReader (boolean):

Description: Render output in plain-text to be more screen reader
accessible

Description: The Gemini model to use for conversations.

Default:undefined

model.maxSessionTurns (number):

Description: Maximum number of user/model/tool turns to keep in a
session. -1 means unlimited.

Default:-1

model.summarizeToolOutput (object):

Description: Enables or disables summarization of tool output. Configure
per-tool token budgets (for example {"run_shell_command": {"tokenBudget":
2000}}). Currently only the run_shell_command tool supports summarization.

Default:undefined

model.compressionThreshold (number):

Description: The fraction of context usage at which to trigger context
compression (e.g. 0.2, 0.3).

Description: Controls how /memory refresh loads GEMINI.md files. When
true, include directories are scanned; when false, only the current
directory is used.

Default:false

context.fileFiltering.respectGitIgnore (boolean):

Description: Respect .gitignore files when searching.

Description: Enable shell output efficiency optimizations for better
performance.

Default:true

tools.autoAccept (boolean):

Description: Automatically accept and execute tool calls that are
considered safe (e.g., read-only operations).

Default:false

tools.core (array):

Description: Restrict the set of built-in tools with an allowlist. Match
semantics mirror tools.allowed; see the built-in tools documentation for
available names.

Default:undefined

Requires restart: Yes

tools.allowed (array):

Description: Tool names that bypass the confirmation dialog. Useful for
trusted commands (for example ["run_shell_command(git)",
"run_shell_command(npm test)"]). See shell tool command restrictions for
matching details.

Default:undefined

Requires restart: Yes

tools.exclude (array):

Description: Tool names to exclude from discovery.

Default:undefined

Requires restart: Yes

tools.discoveryCommand (string):

Description: Command to run for tool discovery.

Default:undefined

Requires restart: Yes

tools.callCommand (string):

Description: Defines a custom shell command for invoking discovered
tools. The command must take the tool name as the first argument, read JSON
arguments from stdin, and emit JSON results on stdout.

Default:undefined

Requires restart: Yes

tools.useRipgrep (boolean):

Description: Use ripgrep for file content search instead of the fallback
implementation. Provides faster search performance.

Default:true

tools.enableToolOutputTruncation (boolean):

Description: Enable truncation of large tool outputs.

Default:true

Requires restart: Yes

tools.truncateToolOutputThreshold (number):

Description: Truncate tool output if it is larger than this many
characters. Set to -1 to disable.

Default:4000000

Requires restart: Yes

tools.truncateToolOutputLines (number):

Description: The number of lines to keep when truncating tool output.

Default:1000

Requires restart: Yes

tools.disableLLMCorrection (boolean):

Description: Disable LLM-based error correction for edit tools. When
enabled, tools will fail immediately if exact string matches are not found,
instead of attempting to self-correct.

Default:false

Requires restart: Yes

tools.enableHooks (boolean):

Description: Enables the hooks system experiment. When disabled, the
hooks system is completely deactivated regardless of other settings.

Configures connections to one or more Model-Context Protocol (MCP) servers for
discovering and using custom tools. Gemini CLI attempts to connect to each
configured MCP server to discover available tools. If multiple MCP servers
expose a tool with the same name, the tool names will be prefixed with the
server alias you defined in the configuration (e.g.,
serverAlias__actualToolName) to avoid conflicts. Note that the system might
strip certain schema properties from MCP tool definitions for compatibility. At
least one of command, url, or httpUrl must be provided. If multiple are
specified, the order of precedence is httpUrl, then url, then command.

mcpServers.<SERVER_NAME> (object): The server parameters for the named
server.

command (string, optional): The command to execute to start the MCP server
via standard I/O.

args (array of strings, optional): Arguments to pass to the command.

env (object, optional): Environment variables to set for the server
process.

cwd (string, optional): The working directory in which to start the
server.

url (string, optional): The URL of an MCP server that uses Server-Sent
Events (SSE) for communication.

httpUrl (string, optional): The URL of an MCP server that uses streamable
HTTP for communication.

headers (object, optional): A map of HTTP headers to send with requests to
url or httpUrl.

timeout (number, optional): Timeout in milliseconds for requests to this
MCP server.

trust (boolean, optional): Trust this server and bypass all tool call
confirmations.

description (string, optional): A brief description of the server, which
may be used for display purposes.

includeTools (array of strings, optional): List of tool names to include
from this MCP server. When specified, only the tools listed here will be
available from this server (allowlist behavior). If not specified, all tools
from the server are enabled by default.

excludeTools (array of strings, optional): List of tool names to exclude
from this MCP server. Tools listed here will not be available to the model,
even if they are exposed by the server. Note:excludeTools takes
precedence over includeTools - if a tool is in both lists, it will be
excluded.

The CLI keeps a history of shell commands you run. To avoid conflicts between
different projects, this history is stored in a project-specific directory
within your user's home folder.

Environment variables are a common way to configure applications, especially for
sensitive information like API keys or for settings that might change between
environments. For authentication setup, see the
Authentication documentation which covers all available
authentication methods.

The CLI automatically loads environment variables from an .env file. The
loading order is:

.env file in the current working directory.

If not found, it searches upwards in parent directories until it finds an
.env file or reaches the project root (identified by a .git folder) or
the home directory.

If still not found, it looks for ~/.env (in the user's home directory).

Environment variable exclusion: Some environment variables (like DEBUG and
DEBUG_MODE) are automatically excluded from being loaded from project .env
files to prevent interference with gemini-cli behavior. Variables from
.gemini/.env files are never excluded. You can customize this behavior using
the advanced.excludedEnvVars setting in your settings.json file.

If using Vertex AI, ensure you have the necessary permissions in this
project.

Cloud Shell note: When running in a Cloud Shell environment, this
variable defaults to a special project allocated for Cloud Shell users. If
you have GOOGLE_CLOUD_PROJECT set in your global environment in Cloud
Shell, it will be overridden by this default. To use a different project in
Cloud Shell, you must define GOOGLE_CLOUD_PROJECT in a .env file.

Writes the current built‑in system prompt to a file for review.

true/1: Write to ./.gemini/system.md. Otherwise treat the value as a
path.

Run the CLI once with this set to generate the file.

SEATBELT_PROFILE (macOS specific):

Switches the Seatbelt (sandbox-exec) profile on macOS.

permissive-open: (Default) Restricts writes to the project folder (and a
few other folders, see
packages/cli/src/utils/sandbox-macos-permissive-open.sb) but allows other
operations.

strict: Uses a strict profile that declines operations by default.

<profile_name>: Uses a custom profile. To define a custom profile, create
a file named sandbox-macos-<profile_name>.sb in your project's .gemini/
directory (e.g., my-project/.gemini/sandbox-macos-custom.sb).

DEBUG or DEBUG_MODE (often used by underlying libraries or the CLI
itself):

Set to true or 1 to enable verbose debug logging, which can be helpful
for troubleshooting.

Note: These variables are automatically excluded from project .env
files by default to prevent interference with gemini-cli behavior. Use
.gemini/.env files if you need to set these for gemini-cli specifically.

NO_COLOR:

Set to any value to disable all color output in the CLI.

CLI_TITLE:

Set to a string to customize the title of the CLI.

CODE_ASSIST_ENDPOINT:

Specifies the endpoint for the code assist server.

To prevent accidental leakage of sensitive information, Gemini CLI automatically
redacts potential secrets from environment variables when executing tools (such
as shell commands). This "best effort" redaction applies to variables inherited
from the system or loaded from .env files.

Default Redaction Rules:

By Name: Variables are redacted if their names contain sensitive terms
like TOKEN, SECRET, PASSWORD, KEY, AUTH, CREDENTIAL, PRIVATE, or
CERT.

By Value: Variables are redacted if their values match known secret
patterns, such as:

Private keys (RSA, OpenSSH, PGP, etc.)

Certificates

URLs containing credentials

API keys and tokens (GitHub, Google, AWS, Stripe, Slack, etc.)

Specific Blocklist: Certain variables like CLIENT_ID, DB_URI,
DATABASE_URL, and CONNECTION_STRING are always redacted by default.

Allowlist (Never Redacted):

Common system variables (e.g., PATH, HOME, USER, SHELL, TERM,
LANG).

Variables starting with GEMINI_CLI_.

GitHub Action specific variables.

Configuration:

You can customize this behavior in your settings.json file:

security.allowedEnvironmentVariables: A list of variable names to
never redact, even if they match sensitive patterns.

security.blockedEnvironmentVariables: A list of variable names to
always redact, even if they don't match sensitive patterns.

While not strictly configuration for the CLI's behavior, context files
(defaulting to GEMINI.md but configurable via the context.fileName setting)
are crucial for configuring the instructional context (also referred to as
"memory") provided to the Gemini model. This powerful feature allows you to give
project-specific instructions, coding style guides, or any relevant background
information to the AI, making its responses more tailored and accurate to your
needs. The CLI includes UI elements, such as an indicator in the footer showing
the number of loaded context files, to keep you informed about the active
context.

Purpose: These Markdown files contain instructions, guidelines, or context
that you want the Gemini model to be aware of during your interactions. The
system is designed to manage this instructional context hierarchically.

Here's a conceptual example of what a context file at the root of a TypeScript
project might contain:

This example demonstrates how you can provide general project context, specific
coding conventions, and even notes about particular files or components. The
more relevant and precise your context files are, the better the AI can assist
you. Project-specific context files are highly encouraged to establish
conventions and context.

Hierarchical loading and precedence: The CLI implements a sophisticated
hierarchical memory system by loading context files (e.g., GEMINI.md) from
several locations. Content from files lower in this list (more specific)
typically overrides or supplements content from files higher up (more
general). The exact concatenation order and final context can be inspected
using the /memory show command. The typical loading order is:

Global context file:

Location: ~/.gemini/<configured-context-filename> (e.g.,
~/.gemini/GEMINI.md in your user home directory).

Scope: Provides default instructions for all your projects.

Project root and ancestors context files:

Location: The CLI searches for the configured context file in the
current working directory and then in each parent directory up to either
the project root (identified by a .git folder) or your home directory.

Scope: Provides context relevant to the entire project or a significant
portion of it.

Sub-directory context files (contextual/local):

Location: The CLI also scans for the configured context file in
subdirectories below the current working directory (respecting common
ignore patterns like node_modules, .git, etc.). The breadth of this
search is limited to 200 directories by default, but can be configured
with the context.discoveryMaxDirs setting in your settings.json
file.

Scope: Allows for highly specific instructions relevant to a particular
component, module, or subsection of your project.

Concatenation and UI indication: The contents of all found context files
are concatenated (with separators indicating their origin and path) and
provided as part of the system prompt to the Gemini model. The CLI footer
displays the count of loaded context files, giving you a quick visual cue
about the active instructional context.

Importing content: You can modularize your context files by importing
other Markdown files using the @path/to/file.md syntax. For more details,
see the Memory Import Processor documentation.

Commands for memory management:

Use /memory refresh to force a re-scan and reload of all context files
from all configured locations. This updates the AI's instructional context.

Use /memory show to display the combined instructional context currently
loaded, allowing you to verify the hierarchy and content being used by the
AI.

See the Commands documentation for full details
on the /memory command and its sub-commands (show and refresh).

By understanding and utilizing these configuration layers and the hierarchical
nature of context files, you can effectively manage the AI's memory and tailor
the Gemini CLI's responses to your specific needs and projects.

The Gemini CLI can execute potentially unsafe operations (like shell commands
and file modifications) within a sandboxed environment to protect your system.

Sandboxing is disabled by default, but you can enable it in a few ways:

Using --sandbox or -s flag.

Setting GEMINI_SANDBOX environment variable.

Sandbox is enabled when using --yolo or --approval-mode=yolo by default.

By default, it uses a pre-built gemini-cli-sandbox Docker image.

For project-specific sandboxing needs, you can create a custom Dockerfile at
.gemini/sandbox.Dockerfile in your project's root directory. This Dockerfile
can be based on the base sandbox image:

When .gemini/sandbox.Dockerfile exists, you can use BUILD_SANDBOX
environment variable when running Gemini CLI to automatically build the custom
sandbox image:

To help us improve the Gemini CLI, we collect anonymized usage statistics. This
data helps us understand how the CLI is used, identify common issues, and
prioritize new features.

What we collect:

Tool calls: We log the names of the tools that are called, whether they
succeed or fail, and how long they take to execute. We do not collect the
arguments passed to the tools or any data returned by them.

API requests: We log the Gemini model used for each request, the duration
of the request, and whether it was successful. We do not collect the content
of the prompts or responses.

Session information: We collect information about the configuration of the
CLI, such as the enabled tools and the approval mode.

What we DON'T collect:

Personally identifiable information (PII): We do not collect any personal
information, such as your name, email address, or API keys.

Prompt and response content: We do not log the content of your prompts or
the responses from the Gemini model.

File content: We do not log the content of any files that are read or
written by the CLI.

How to opt out:

You can opt out of usage statistics collection at any time by setting the
usageStatisticsEnabled property to false under the privacy category in
your settings.json file:

This website uses cookies from Google to deliver and enhance the quality of its services and to analyze
traffic.