---
url: https://geminicli.com/docs/cli/uninstall
title: Uninstalling the CLI
author: null
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

Your uninstall method depends on how you ran the CLI. Follow the instructions for either npx or a global npm installation.

npx runs packages from a temporary cache without a permanent installation. To "uninstall" the CLI, you must clear this cache, which will remove gemini-cli and any other packages previously executed with npx.

The npx cache is a directory named `_npx`

inside your main npm cache folder. You
can find your npm cache path by running `npm config get cache`

.

**For macOS / Linux**

**For Windows**

*Command Prompt*

*PowerShell*

If you installed the CLI globally (e.g., `npm install -g @google/gemini-cli`

),
use the `npm uninstall`

command with the `-g`

flag to remove it.

This command completely removes the package from your system.