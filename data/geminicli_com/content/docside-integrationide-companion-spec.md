---
url: https://geminicli.com/docs/ide-integration/ide-companion-spec
title: 'Gemini CLI companion plugin: Interface specification'
author: null
date: '2025-09-15'
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

Last Updated: September 15, 2025

This document defines the contract for building a companion plugin to enable Gemini CLI's IDE mode. For VS Code, these features (native diffing, context awareness) are provided by the official extension (marketplace). This specification is for contributors who wish to bring similar functionality to other editors like JetBrains IDEs, Sublime Text, etc.

Gemini CLI and the IDE plugin communicate through a local communication channel.

The plugin **MUST** run a local HTTP server that implements the **Model Context
Protocol (MCP)**.

`/mcp`

) for
all MCP communication.`0`

).For Gemini CLI to connect, it needs to discover which IDE instance it's running
in and what port your server is using. The plugin **MUST** facilitate this by
creating a "discovery file."

**How the CLI finds the file:** The CLI determines the Process ID (PID) of the
IDE it's running in by traversing the process tree. It then looks for a
discovery file that contains this PID in its name.

**File location:** The file must be created in a specific directory:
`os.tmpdir()/gemini/ide/`

. Your plugin must create this directory if it
doesn't exist.

**File naming convention:** The filename is critical and **MUST** follow the
pattern: `gemini-ide-server-${PID}-${PORT}.json`

`${PID}`

: The process ID of the parent IDE process. Your plugin must
determine this PID and include it in the filename.`${PORT}`

: The port your MCP server is listening on.**File content and workspace validation:** The file **MUST** contain a JSON
object with the following structure:

`port`

(number, required): The port of the MCP server.`workspacePath`

(string, required): A list of all open workspace root paths,
delimited by the OS-specific path separator (`:`

for Linux/macOS, `;`

for
Windows). The CLI uses this path to ensure it's running in the same project
folder that's open in the IDE. If the CLI's current working directory is not
a sub-directory of `workspacePath`

, the connection will be rejected. Your
plugin `authToken`

(string, required): A secret token for securing the connection.
The CLI will include this token in an `Authorization: Bearer <token>`

header
on all requests.`ideInfo`

(object, required): Information about the IDE.
`name`

(string, required): A short, lowercase identifier for the IDE
(e.g., `vscode`

, `jetbrains`

).`displayName`

(string, required): A user-friendly name for the IDE (e.g.,
`VS Code`

, `JetBrains IDE`

).**Authentication:** To secure the connection, the plugin **MUST** generate a
unique, secret token and include it in the discovery file. The CLI will then
include this token in the `Authorization`

header for all requests to the MCP
server (e.g., `Authorization: Bearer a-very-secret-token`

). Your server
**MUST** validate this token on every request and reject any that are
unauthorized.

**Tie-breaking with environment variables (recommended):** For the most
reliable experience, your plugin **SHOULD** both create the discovery file and
set the `GEMINI_CLI_IDE_SERVER_PORT`

environment variable in the integrated
terminal. The file serves as the primary discovery mechanism, but the
environment variable is crucial for tie-breaking. If a user has multiple IDE
windows open for the same workspace, the CLI uses the
`GEMINI_CLI_IDE_SERVER_PORT`

variable to identify and connect to the correct
window's server.

To enable context awareness, the plugin **MAY** provide the CLI with real-time
information about the user's activity in the IDE.

`ide/contextUpdate`

notificationThe plugin **MAY** send an `ide/contextUpdate`

notification
to the CLI whenever the user's context changes.

**Triggering events:** This notification should be sent (with a recommended
debounce of 50ms) when:

**Payload ( IdeContext):** The notification parameters

`IdeContext`

object:**Note:** The `openFiles`

list should only include files that exist on disk.
Virtual files (e.g., unsaved files without a path, editor settings pages)
**MUST** be excluded.

After receiving the `IdeContext`

object, the CLI performs several normalization
and truncation steps before sending the information to the model.

`timestamp`

field to determine the most
recently used files. It sorts the `openFiles`

list based on this value.
Therefore, your plugin `isActive`

flag on all other files
and clear their `cursor`

and `selectedText`

fields. Your plugin should focus
on setting `isActive: true`

and providing cursor/selection details only for
the currently focused file.`selectedText`

(to 16KB).While the CLI handles the final truncation, it is highly recommended that your plugin also limits the amount of context it sends.

To enable interactive code modifications, the plugin **MAY** expose a diffing
interface. This allows the CLI to request that the IDE open a diff view, showing
proposed changes to a file. The user can then review, edit, and ultimately
accept or reject these changes directly within the IDE.

`openDiff`

toolThe plugin **MUST** register an `openDiff`

tool on its MCP server.

**Description:** This tool instructs the IDE to open a modifiable diff view
for a specific file.

**Request ( OpenDiffRequest):** The tool is invoked via a

`tools/call`

request. The `arguments`

field within the request's `params`

`OpenDiffRequest`

object.**Response ( CallToolResult):** The tool

`CallToolResult`

to acknowledge the request and report whether the diff view
was successfully opened.`content: []`

).`isError: true`

and include a `TextContent`

block in the
`content`

array describing the error.The actual outcome of the diff (acceptance or rejection) is communicated asynchronously via notifications.

`closeDiff`

toolThe plugin **MUST** register a `closeDiff`

tool on its MCP server.

**Description:** This tool instructs the IDE to close an open diff view for a
specific file.

**Request ( CloseDiffRequest):** The tool is invoked via a

`tools/call`

request. The `arguments`

field within the request's `params`

`CloseDiffRequest`

object.**Response ( CallToolResult):** The tool

`CallToolResult`

.`isError: true`

and include a `TextContent`

block in the
`content`

array describing the error.`ide/diffAccepted`

notificationWhen the user accepts the changes in a diff view (e.g., by clicking an "Apply"
or "Save" button), the plugin **MUST** send an `ide/diffAccepted`

notification
to the CLI.

**Payload:** The notification parameters **MUST** include the file path and
the final content of the file. The content may differ from the original
`newContent`

if the user made manual edits in the diff view.

`ide/diffRejected`

notificationWhen the user rejects the changes (e.g., by closing the diff view without
accepting), the plugin **MUST** send an `ide/diffRejected`

notification to the
CLI.

**Payload:** The notification parameters **MUST** include the file path of the
rejected diff.

The plugin **MUST** manage its resources and the discovery file correctly based
on the IDE's lifecycle.