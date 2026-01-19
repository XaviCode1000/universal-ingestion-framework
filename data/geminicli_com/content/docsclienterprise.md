---
url: https://geminicli.com/docs/cli/enterprise
title: Gemini CLI for the enterprise
author: null
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

This document outlines configuration patterns and best practices for deploying and managing Gemini CLI in an enterprise environment. By leveraging system-level settings, administrators can enforce security policies, manage tool access, and ensure a consistent experience for all users.

A note on security:The patterns described in this document are intended to help administrators create a more controlled and secure environment for using Gemini CLI. However, they should not be considered a foolproof security boundary. A determined user with sufficient privileges on their local machine may still be able to circumvent these configurations. These measures are designed to prevent accidental misuse and enforce corporate policy in a managed environment, not to defend against a malicious actor with local administrative rights.

The most powerful tools for enterprise administration are the system-wide
settings files. These files allow you to define a baseline configuration
(`system-defaults.json`

) and a set of overrides (`settings.json`

) that apply to
all users on a machine. For a complete overview of configuration options, see
the Configuration documentation.

Settings are merged from four files. The precedence order for single-value
settings (like `theme`

) is:

`system-defaults.json`

)`~/.gemini/settings.json`

)`<project>/.gemini/settings.json`

)`settings.json`

)This means the System Overrides file has the final say. For settings that are
arrays (`includeDirectories`

) or objects (`mcpServers`

), the values are merged.

**Example of merging and precedence:**

Here is how settings from different levels are combined.

**System defaults system-defaults.json:**

**User settings.json (~/.gemini/settings.json):**

**Workspace settings.json (<project>/.gemini/settings.json):**

**System overrides settings.json:**

This results in the following merged configuration:

**Why:**

** theme**: The value from the system overrides (

`system-enforced-theme`

) is
used, as it has the highest precedence.** mcpServers**: The objects are merged. The

`corp-server`

definition from
the system overrides takes precedence over the user's definition. The unique
`user-tool`

and `project-tool`

are included.** includeDirectories**: The arrays are concatenated in the order of System
Defaults, User, Workspace, and then System Overrides.

**Location**:

`/etc/gemini-cli/settings.json`

`C:\ProgramData\gemini-cli\settings.json`

`/Library/Application Support/GeminiCli/settings.json`

`GEMINI_CLI_SYSTEM_SETTINGS_PATH`

environment variable.**Control**: This file should be managed by system administrators and
protected with appropriate file permissions to prevent unauthorized
modification by users.

By using the system settings file, you can enforce the security and configuration patterns described below.

While the `GEMINI_CLI_SYSTEM_SETTINGS_PATH`

environment variable provides
flexibility, a user could potentially override it to point to a different
settings file, bypassing the centrally managed configuration. To mitigate this,
enterprises can deploy a wrapper script or alias that ensures the environment
variable is always set to the corporate-controlled path.

This approach ensures that no matter how the user calls the `gemini`

command,
the enterprise settings are always loaded with the highest precedence.

**Example wrapper script:**

Administrators can create a script named `gemini`

and place it in a directory
that appears earlier in the user's `PATH`

than the actual Gemini CLI binary
(e.g., `/usr/local/bin/gemini`

).

By deploying this script, the `GEMINI_CLI_SYSTEM_SETTINGS_PATH`

is set within
the script's environment, and the `exec`

command replaces the script process
with the actual Gemini CLI process, which inherits the environment variable.
This makes it significantly more difficult for a user to bypass the enforced
settings.

You can significantly enhance security by controlling which tools the Gemini
model can use. This is achieved through the `tools.core`

and `tools.exclude`

settings. For a list of available tools, see the
Tools documentation.

`coreTools`

The most secure approach is to explicitly add the tools and commands that users are permitted to execute to an allowlist. This prevents the use of any tool not on the approved list.

**Example:** Allow only safe, read-only file operations and listing files.

`excludeTools`

Alternatively, you can add specific tools that are considered dangerous in your environment to a blocklist.

**Example:** Prevent the use of the shell tool for removing files.

**Security note:** Blocklisting with `excludeTools`

is less secure than
allowlisting with `coreTools`

, as it relies on blocking known-bad commands, and
clever users may find ways to bypass simple string-based blocks. **Allowlisting
is the recommended approach.**

To ensure that users cannot bypass the confirmation prompt for tool execution, you can disable YOLO mode at the policy level. This adds a critical layer of safety, as it prevents the model from executing tools without explicit user approval.

**Example:** Force all tool executions to require user confirmation.

This setting is highly recommended in an enterprise environment to prevent unintended tool execution.

If your organization uses custom tools via Model-Context Protocol (MCP) servers, it is crucial to understand how server configurations are managed to apply security policies effectively.

Gemini CLI loads `settings.json`

files from three levels: System, Workspace, and
User. When it comes to the `mcpServers`

object, these configurations are
**merged**:

`corp-api`

exists in both system and user
settings), the definition from the highest-precedence level is used. The
order of precedence is: This means a user **cannot** override the definition of a server that is already
defined in the system-level settings. However, they **can** add new servers with
unique names.

The security of your MCP tool ecosystem depends on a combination of defining the canonical servers and adding their names to an allowlist.

For even greater security, especially when dealing with third-party MCP servers,
you can restrict which specific tools from a server are exposed to the model.
This is done using the `includeTools`

and `excludeTools`

properties within a
server's definition. This allows you to use a subset of tools from a server
without allowing potentially dangerous ones.

Following the principle of least privilege, it is highly recommended to use
`includeTools`

to create an allowlist of only the necessary tools.

**Example:** Only allow the `code-search`

and `get-ticket-details`

tools from a
third-party MCP server, even if the server offers other tools like
`delete-ticket`

.

To create a secure, centrally-managed catalog of tools, the system administrator
**must** do both of the following in the system-level `settings.json`

file:

`mcpServers`

object. This ensures that even if a user defines a server with
the same name, the secure system-level definition will take precedence.`mcp.allowed`

setting. This is a critical security step that prevents users from running
any servers that are not on this list. If this setting is omitted, the CLI
will merge and allow any server defined by the user.**Example system settings.json:**

Add the *names* of all approved servers to an allowlist. This will prevent
users from adding their own servers.

Provide the canonical *definition* for each server on the allowlist.

This pattern is more secure because it uses both definition and an allowlist.
Any server a user defines will either be overridden by the system definition (if
it has the same name) or blocked because its name is not in the `mcp.allowed`

list.

If the administrator defines the `mcpServers`

object but fails to also specify
the `mcp.allowed`

allowlist, users may add their own servers.

**Example system settings.json:**

This configuration defines servers but does not enforce the allowlist. The administrator has NOT included the "mcp.allowed" setting.

In this scenario, a user can add their own server in their local
`settings.json`

. Because there is no `mcp.allowed`

list to filter the merged
results, the user's server will be added to the list of available tools and
allowed to run.

To mitigate the risk of potentially harmful operations, you can enforce the use of sandboxing for all tool execution. The sandbox isolates tool execution in a containerized environment.

**Example:** Force all tool execution to happen within a Docker sandbox.

You can also specify a custom, hardened Docker image for the sandbox by building
a custom `sandbox.Dockerfile`

as described in the
Sandboxing documentation.

In corporate environments with strict network policies, you can configure Gemini
CLI to route all outbound traffic through a corporate proxy. This can be set via
an environment variable, but it can also be enforced for custom tools via the
`mcpServers`

configuration.

**Example (for an MCP server):**

For auditing and monitoring purposes, you can configure Gemini CLI to send telemetry data to a central location. This allows you to track tool usage and other events. For more information, see the telemetry documentation.

**Example:** Enable telemetry and send it to a local OTLP collector. If
`otlpEndpoint`

is not specified, it defaults to `http://localhost:4317`

.

**Note:** Ensure that `logPrompts`

is set to `false`

in an enterprise setting to
avoid collecting potentially sensitive information from user prompts.

You can enforce a specific authentication method for all users by setting the
`enforcedAuthType`

in the system-level `settings.json`

file. This prevents users
from choosing a different authentication method. See the
Authentication docs for more details.

**Example:** Enforce the use of Google login for all users.

If a user has a different authentication method configured, they will be prompted to switch to the enforced method. In non-interactive mode, the CLI will exit with an error if the configured authentication method does not match the enforced one.

For enterprises using Google Workspace, you can enforce that users only authenticate with their corporate Google accounts. This is a network-level control that is configured on a proxy server, not within Gemini CLI itself. It works by intercepting authentication requests to Google and adding a special HTTP header.

This policy prevents users from logging in with personal Gmail accounts or other non-corporate Google accounts.

For detailed instructions, see the Google Workspace Admin Help article on blocking access to consumer accounts.

The general steps are as follows:

`google.com`

.`X-GoogApps-Allowed-Domains`

HTTP header.**Example header:**

When this header is present, Google's authentication service will only allow logins from accounts belonging to the specified domains.

`settings.json`

Here is an example of a system `settings.json`

file that combines several of the
patterns discussed above to create a secure, controlled environment for Gemini
CLI.

This configuration:

`/bug`

command to an internal ticketing system.