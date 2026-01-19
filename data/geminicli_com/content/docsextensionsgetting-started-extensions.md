---
url: https://geminicli.com/docs/extensions/getting-started-extensions
title: Getting started with Gemini CLI extensions
author: null
date: '2025-01-01'
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

This guide will walk you through creating your first Gemini CLI extension.
You'll learn how to set up a new extension, add a custom tool via an MCP server,
create a custom command, and provide context to the model with a `GEMINI.md`

file.

Before you start, make sure you have the Gemini CLI installed and a basic understanding of Node.js and TypeScript.

The easiest way to start is by using one of the built-in templates. We'll use
the `mcp-server`

example as our foundation.

Run the following command to create a new directory called `my-first-extension`

with the template files:

This will create a new directory with the following structure:

Let's look at the key files in your new extension.

`gemini-extension.json`

This is the manifest file for your extension. It tells Gemini CLI how to load and use your extension.

`name`

: The unique name for your extension.`version`

: The version of your extension.`mcpServers`

: This section defines one or more Model Context Protocol (MCP)
servers. MCP servers are how you can add new tools for the model to use.
`command`

, `args`

, `cwd`

: These fields specify how to start your server.
Notice the use of the `${extensionPath}`

variable, which Gemini CLI replaces
with the absolute path to your extension's installation directory. This
allows your extension to work regardless of where it's installed.`example.ts`

This file contains the source code for your MCP server. It's a simple Node.js
server that uses the `@modelcontextprotocol/sdk`

.

This server defines a single tool called `fetch_posts`

that fetches data from a
public API.

`package.json`

and `tsconfig.json`

These are standard configuration files for a TypeScript project. The
`package.json`

file defines dependencies and a `build`

script, and
`tsconfig.json`

configures the TypeScript compiler.

Before you can use the extension, you need to compile the TypeScript code and link the extension to your Gemini CLI installation for local development.

**Install dependencies:**

**Build the server:**

This will compile `example.ts`

into `dist/example.js`

, which is the file
referenced in your `gemini-extension.json`

.

**Link the extension:**

The `link`

command creates a symbolic link from the Gemini CLI extensions
directory to your development directory. This means any changes you make
will be reflected immediately without needing to reinstall.

Now, restart your Gemini CLI session. The new `fetch_posts`

tool will be
available. You can test it by asking: "fetch posts".

Custom commands provide a way to create shortcuts for complex prompts. Let's add a command that searches for a pattern in your code.

Create a `commands`

directory and a subdirectory for your command group:

Create a file named `commands/fs/grep-code.toml`

:

This command, `/fs:grep-code`

, will take an argument, run the `grep`

shell
command with it, and pipe the results into a prompt for summarization.

After saving the file, restart the Gemini CLI. You can now run
`/fs:grep-code "some pattern"`

to use your new command.

`GEMINI.md`

You can provide persistent context to the model by adding a `GEMINI.md`

file to
your extension. This is useful for giving the model instructions on how to
behave or information about your extension's tools. Note that you may not always
need this for extensions built to expose commands and prompts.

Create a file named `GEMINI.md`

in the root of your extension directory:

Update your `gemini-extension.json`

to tell the CLI to load this file:

Restart the CLI again. The model will now have the context from your `GEMINI.md`

file in every session where the extension is active.

*Note: This is an experimental feature enabled via experimental.skills.*

Agent Skills let you bundle specialized expertise and
procedural workflows. Unlike `GEMINI.md`

, which provides persistent context,
skills are activated only when needed, saving context tokens.

Create a `skills`

directory and a subdirectory for your skill:

Create a `skills/security-audit/SKILL.md`

file:

Skills bundled with your extension are automatically discovered and can be activated by the model during a session when it identifies a relevant task.

Once you're happy with your extension, you can share it with others. The two primary ways of releasing extensions are via a Git repository or through GitHub Releases. Using a public Git repository is the simplest method.

For detailed instructions on both methods, please refer to the Extension Releasing Guide.

You've successfully created a Gemini CLI extension! You learned how to:

From here, you can explore more advanced features and build powerful new capabilities into the Gemini CLI.