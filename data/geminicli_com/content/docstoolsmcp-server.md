---
url: https://geminicli.com/docs/tools/mcp-server
title: MCP servers with the Gemini CLI
author: null
date: '2025-06-18'
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

An MCP server is an application that exposes tools and resources to the Gemini
CLI through the Model Context Protocol, allowing it to interact with external
systems and data sources. MCP servers act as a bridge between the Gemini model
and your local environment or other services like APIs.

An MCP server enables the Gemini CLI to:

Discover tools: List available tools, their descriptions, and parameters
through standardized schema definitions.

Execute tools: Call specific tools with defined arguments and receive
structured responses.

Access resources: Read data from specific resources that the server
exposes (files, API payloads, reports, etc.).

With an MCP server, you can extend the Gemini CLI's capabilities to perform
actions beyond its built-in features, such as interacting with databases, APIs,
custom scripts, or specialized workflows.

The Gemini CLI integrates with MCP servers through a sophisticated discovery and
execution system built into the core package (packages/core/src/tools/):

Some MCP servers expose contextual "resources" in addition to the tools and
prompts. Gemini CLI discovers these automatically and gives you the possibility
to reference them in the chat.

You can use the same @ syntax already known for referencing local files:

Resource URIs appear in the completion menu together with filesystem paths. When
you submit the message, the CLI calls resources/read and injects the content
in the conversation.

The Gemini CLI uses the mcpServers configuration in your settings.json file
to locate and connect to MCP servers. This configuration supports multiple
servers with different transport mechanisms.

You can configure MCP servers in your settings.json file in two main ways:
through the top-level mcpServers object for specific server definitions, and
through the mcp object for global settings that control server discovery and
execution.

The mcp object in your settings.json allows you to define global rules for
all MCP servers.

mcp.serverCommand (string): A global command to start an MCP server.

mcp.allowed (array of strings): A list of MCP server names to allow. If
this is set, only servers from this list (matching the keys in the
mcpServers object) will be connected to.

mcp.excluded (array of strings): A list of MCP server names to exclude.
Servers in this list will not be connected to.

trust (boolean): When true, bypasses all tool call confirmations for
this server (default: false)

includeTools (string[]): List of tool names to include from this MCP
server. When specified, only the tools listed here will be available from this
server (allowlist behavior). If not specified, all tools from the server are
enabled by default.

excludeTools (string[]): List of tool names to exclude from this MCP
server. Tools listed here will not be available to the model, even if they are
exposed by the server. Note:excludeTools takes precedence over
includeTools - if a tool is in both lists, it will be excluded.

targetAudience (string): The OAuth Client ID allowlisted on the
IAP-protected application you are trying to access. Used with
authProviderType: 'service_account_impersonation'.

targetServiceAccount (string): The email address of the Google Cloud
Service Account to impersonate. Used with
authProviderType: 'service_account_impersonation'.

The Gemini CLI supports OAuth 2.0 authentication for remote MCP servers using
SSE or HTTP transports. This enables secure access to MCP servers that require
authentication.

You can specify the authentication provider type using the authProviderType
property:

authProviderType (string): Specifies the authentication provider. Can be
one of the following:

dynamic_discovery (default): The CLI will automatically discover the
OAuth configuration from the server.

google_credentials: The CLI will use the Google Application Default
Credentials (ADC) to authenticate with the server. When using this provider,
you must specify the required scopes.

service_account_impersonation: The CLI will impersonate a Google Cloud
Service Account to authenticate with the server. This is useful for
accessing IAP-protected services (this was specifically designed for Cloud
Run services).

To authenticate with a server using Service Account Impersonation, you must set
the authProviderType to service_account_impersonation and provide the
following properties:

targetAudience (string): The OAuth Client ID allowslisted on the
IAP-protected application you are trying to access.

targetServiceAccount (string): The email address of the Google Cloud
Service Account to impersonate.

The CLI will use your local Application Default Credentials (ADC) to generate an
OIDC ID token for the specified service account and audience. This token will
then be used to authenticate with the MCP server.

Create or use an
existing OAuth 2.0 client ID. To use an existing OAuth 2.0 client ID,
follow the steps in
How to share OAuth Clients.

Add the OAuth ID to the allowlist for
programmatic access
for the application. Since Cloud Run is not yet a supported resource type
in gcloud iap, you must allowlist the Client ID on the project.

Add both the service account and users to the IAP Policy in the
"Security" tab of the Cloud Run service itself or via gcloud.

Grant all users and groups who will access the MCP Server the necessary
permissions to
impersonate the service account
(i.e., roles/iam.serviceAccountTokenCreator).

Property stripping: The system automatically removes certain schema
properties ($schema, additionalProperties) for Gemini API compatibility

Name sanitization: Tool names are automatically sanitized to meet API
requirements

Conflict resolution: Tool name conflicts between servers are resolved
through automatic prefixing

This comprehensive integration makes MCP servers a powerful way to extend the
Gemini CLI's capabilities while maintaining security, reliability, and ease of
use.

MCP tools are not limited to returning simple text. You can return rich,
multi-part content, including text, images, audio, and other binary data in a
single tool response. This allows you to build powerful tools that can provide
diverse information to the model in a single turn.

All data returned from the tool is processed and sent to the model as context
for its next generation, enabling it to reason about or summarize the provided
information.

To return rich content, your tool's response must adhere to the MCP
specification for a
CallToolResult.
The content field of the result should be an array of ContentBlock objects.
The Gemini CLI will correctly process this array, separating text from binary
data and packaging it for the model.

You can mix and match different content block types in the content array. The
supported block types include:

In addition to tools, MCP servers can expose predefined prompts that can be
executed as slash commands within the Gemini CLI. This allows you to create
shortcuts for common or complex queries that can be easily invoked by name.

Once a prompt is discovered, you can invoke it using its name as a slash
command. The CLI will automatically handle parsing arguments.

or, using positional arguments:

When you run this command, the Gemini CLI executes the prompts/get method on
the MCP server with the provided arguments. The server is responsible for
substituting the arguments into the prompt template and returning the final
prompt text. The CLI then sends this prompt to the model for execution. This
provides a convenient way to automate and share common workflows.

While you can always configure MCP servers by manually editing your
settings.json file, the Gemini CLI provides a convenient set of commands to
manage your server configurations programmatically. These commands streamline
the process of adding, listing, and removing MCP servers without needing to
directly edit JSON files.

The add command configures a new MCP server in your settings.json. Based on
the scope (-s, --scope), it will be added to either the user config
~/.gemini/settings.json or the project config .gemini/settings.json file.

Command:

<name>: A unique name for the server.

<commandOrUrl>: The command to execute (for stdio) or the URL (for
http/sse).

[args...]: Optional arguments for a stdio command.

Options (flags):

-s, --scope: Configuration scope (user or project). [default: "project"]

-t, --transport: Transport type (stdio, sse, http). [default: "stdio"]

-e, --env: Set environment variables (e.g. -e KEY=value).

-H, --header: Set HTTP headers for SSE and HTTP transports (e.g. -H
"X-Api-Key: abc123" -H "Authorization: Bearer abc123").

--timeout: Set connection timeout in milliseconds.

--trust: Trust the server (bypass all tool call confirmation prompts).

--description: Set the description for the server.

--include-tools: A comma-separated list of tools to include.

--exclude-tools: A comma-separated list of tools to exclude.

To view all MCP servers currently configured, use the list command. It
displays each server's name, configuration details, and connection status. This
command has no flags.