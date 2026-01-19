---
url: https://geminicli.com/docs/cli/session-management/
title: Session Management
author: null
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

Gemini CLI includes robust session management features that automatically save your conversation history. This allows you to interrupt your work and resume exactly where you left off, review past interactions, and manage your conversation history effectively.

Every time you interact with Gemini CLI, your session is automatically saved. This happens in the background without any manual intervention.

`~/.gemini/tmp/<project_hash>/chats/`

.You can resume a previous session to continue the conversation with all prior context restored.

When starting the CLI, you can use the `--resume`

(or `-r`

) flag:

**Resume latest:**

This immediately loads the most recent session.

**Resume by index:** First, list available sessions (see
Listing Sessions), then use the index number:

**Resume by ID:** You can also provide the full session UUID:

While the CLI is running, you can use the `/resume`

slash command to open the
**Session Browser**:

This opens an interactive interface where you can:

`/`

to enter search mode, then type to filter sessions by ID
or content.`Enter`

to resume the selected session.To see a list of all available sessions for the current project from the command line:

Output example:

You can remove old or unwanted sessions to free up space or declutter your history.

**From the Command Line:** Use the `--delete-session`

flag with an index or ID:

**From the Session Browser:**

`/resume`

.`x`

.You can configure how Gemini CLI manages your session history in your
`settings.json`

file.

To prevent your history from growing indefinitely, you can enable automatic cleanup policies.

`enabled`

`false`

.`maxAge`

`maxCount`

`minRetention`

`"1d"`

; sessions newer than this period are never deleted by automatic
cleanup.You can also limit the length of individual sessions to prevent context windows from becoming too large and expensive.

** maxSessionTurns**: (number) The maximum number of turns (user + model
exchanges) allowed in a single session. Set to

`-1`

for unlimited (default).**Behavior when limit is reached:**