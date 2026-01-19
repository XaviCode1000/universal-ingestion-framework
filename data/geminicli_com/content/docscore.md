---
url: https://geminicli.com/docs/core
title: Gemini CLI core
author: null
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

Gemini CLI's core package (`packages/core`

) is the backend portion of Gemini
CLI, handling communication with the Gemini API, managing tools, and processing
requests sent from `packages/cli`

. For a general overview of Gemini CLI, see the
main documentation page.

While the `packages/cli`

portion of Gemini CLI provides the user interface,
`packages/core`

is responsible for:

`GEMINI.md`

files.The core plays a vital role in security:

`GEMINI_API_KEY`

and ensures it's used
securely when communicating with the Gemini API.`run_shell_command`

), the core (and its underlying tool implementations) must
do so with appropriate caution, often involving sandboxing mechanisms to
prevent unintended modifications.To ensure that long conversations don't exceed the token limits of the Gemini model, the core includes a chat history compression feature.

When a conversation approaches the token limit for the configured model, the core automatically compresses the conversation history before sending it to the model. This compression is designed to be lossless in terms of the information conveyed, but it reduces the overall number of tokens used.

You can find the token limits for each model in the Google AI documentation.

Gemini CLI includes a model fallback mechanism to ensure that you can continue to use the CLI even if the default "pro" model is rate-limited.

If you are using the default "pro" model and the CLI detects that you are being rate-limited, it automatically switches to the "flash" model for the current session. This allows you to continue working without interruption.

The file discovery service is responsible for finding files in the project that
are relevant to the current context. It is used by the `@`

command and other
tools that need to access files.

The memory discovery service is responsible for finding and loading the
`GEMINI.md`

files that provide context to the model. It searches for these files
in a hierarchical manner, starting from the current working directory and moving
up to the project root and the user's home directory. It also searches in
subdirectories.

This allows you to have global, project-level, and component-level context files, which are all combined to provide the model with the most relevant information.

You can use the `/memory`

command to `show`

, `add`

, and
`refresh`

the content of loaded `GEMINI.md`

files.

When Gemini finds it is reciting text from a source it appends the citation to the output. It is enabled by default but can be disabled with the ui.showCitations setting.