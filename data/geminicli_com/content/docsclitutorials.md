---
url: https://geminicli.com/docs/cli/tutorials
title: Tutorials
author: null
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

This page contains tutorials for interacting with Gemini CLI.

[!CAUTION] Before using a third-party MCP server, ensure you trust its source and understand the tools it provides. Your use of third-party servers is at your own risk.

This tutorial demonstrates how to set up an MCP server, using the GitHub MCP server as an example. The GitHub MCP server provides tools for interacting with GitHub repositories, such as creating issues and commenting on pull requests.

Before you begin, ensure you have the following installed and configured:

`settings.json`

In your project's root directory, create or open the
`.gemini/settings.json`

file. Within the
file, add the `mcpServers`

configuration block, which provides instructions for
how to launch the GitHub MCP server.

[!CAUTION] Using a broadly scoped personal access token that has access to personal and private repositories can lead to information from the private repository being leaked into the public repository. We recommend using a fine-grained access token that doesn't share access to both public and private repositories.

Use an environment variable to store your GitHub PAT:

Gemini CLI uses this value in the `mcpServers`

configuration that you defined in
the `settings.json`

file.

When you launch Gemini CLI, it automatically reads your configuration and launches the GitHub MCP server in the background. You can then use natural language prompts to ask Gemini CLI to perform GitHub actions. For example: