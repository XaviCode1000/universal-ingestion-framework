---
url: https://geminicli.com/docs/ide-integration
title: IDE integration
author: null
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

Gemini CLI can integrate with your IDE to provide a more seamless and context-aware experience. This integration allows the CLI to understand your workspace better and enables powerful features like native in-editor diffing.

Currently, the supported IDEs are Antigravity, Visual Studio Code, and other editors that support VS Code extensions. To build support for other editors, see the IDE Companion Extension Spec.

**Workspace context:** The CLI automatically gains awareness of your workspace
to provide more relevant and accurate responses. This context includes:

**Native diffing:** When Gemini suggests code modifications, you can view the
changes directly within your IDE's native diff viewer. This allows you to
review, edit, and accept or reject the suggested changes seamlessly.

**VS Code commands:** You can access Gemini CLI features directly from the VS
Code Command Palette (`Cmd+Shift+P`

or `Ctrl+Shift+P`

):

`Gemini CLI: Run`

: Starts a new Gemini CLI session in the integrated
terminal.`Gemini CLI: Accept Diff`

: Accepts the changes in the active diff editor.`Gemini CLI: Close Diff Editor`

: Rejects the changes and closes the active
diff editor.`Gemini CLI: View Third-Party Notices`

: Displays the third-party notices for
the extension.There are three ways to set up the IDE integration:

When you run Gemini CLI inside a supported editor, it will automatically detect your environment and prompt you to connect. Answering "Yes" will automatically run the necessary setup, which includes installing the companion extension and enabling the connection.

If you previously dismissed the prompt or want to install the extension manually, you can run the following command inside Gemini CLI:

This will find the correct extension for your IDE and install it.

You can also install the extension directly from a marketplace.

NOTE: The "Gemini CLI Companion" extension may appear towards the bottom of search results. If you don't see it immediately, try scrolling down or sorting by "Newly Published".

After manually installing the extension, you must run

`/ide enable`

in the CLI to activate the integration.

You can control the IDE integration from within the CLI:

When enabled, Gemini CLI will automatically attempt to connect to the IDE companion extension.

To check the connection status and see the context the CLI has received from the IDE, run:

If connected, this command will show the IDE it's connected to and a list of recently opened files it is aware of.

[!NOTE] The file list is limited to 10 recently accessed files within your workspace and only includes local files on disk.)

When you ask Gemini to modify a file, it can open a diff view directly in your editor.

**To accept a diff**, you can perform any of the following actions:

`Cmd+S`

or `Ctrl+S`

).`yes`

in the CLI when prompted.**To reject a diff**, you can:

`no`

in the CLI when prompted.You can also **modify the suggested changes** directly in the diff view before
accepting them.

If you select 'Allow for this session' in the CLI, changes will no longer show up in the IDE as they will be auto-accepted.

If you are using Gemini CLI within a sandbox, please be aware of the following:

`host.docker.internal`

. No special configuration is usually
required, but you may need to ensure your Docker networking setup allows
connections from the container to the host.If you encounter issues with IDE integration, here are some common error messages and how to resolve them.

**Message:**
`🔴 Disconnected: Failed to connect to IDE companion extension in [IDE Name]. Please ensure the extension is running. To install the extension, run /ide install.`

`GEMINI_CLI_IDE_WORKSPACE_PATH`

or `GEMINI_CLI_IDE_SERVER_PORT`

) to connect
to the IDE. This usually means the IDE companion extension is not running or
did not initialize correctly.**Message:**
`🔴 Disconnected: IDE connection error. The connection was lost unexpectedly. Please try reconnecting by running /ide enable`

`/ide enable`

to try and reconnect. If the issue
continues, open a new terminal window or restart your IDE.**Message:**
`🔴 Disconnected: Directory mismatch. Gemini CLI is running in a different location than the open workspace in [IDE Name]. Please run the CLI from one of the following directories: [List of directories]`

`cd`

into the same directory that is open in your IDE and
restart the CLI.**Message:**
`🔴 Disconnected: To use this feature, please open a workspace folder in [IDE Name] and try again.`

**Message:**
`IDE integration is not supported in your current environment. To use this feature, run Gemini CLI in one of these supported IDEs: [List of IDEs]`

**Message:**
`No installer is available for IDE. Please install the Gemini CLI Companion extension manually from the marketplace.`

`/ide install`

, but the CLI does not have an automated
installer for your specific IDE.