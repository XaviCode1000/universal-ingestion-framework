---
url: https://geminicli.com/docs/cli/trusted-folders
title: Trusted Folders
author: null
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

The Trusted Folders feature is a security setting that gives you control over which projects can use the full capabilities of the Gemini CLI. It prevents potentially malicious code from running by asking you to approve a folder before the CLI loads any project-specific configurations from it.

The Trusted Folders feature is **disabled by default**. To use it, you must
first enable it in your settings.

Add the following to your user `settings.json`

file:

Once the feature is enabled, the first time you run the Gemini CLI from a folder, a dialog will automatically appear, prompting you to make a choice:

`my-project`

).`safe-projects`

), which automatically trusts all of its subdirectories as
well. This is useful if you keep all your safe projects in one place.Your choice is saved in a central file (`~/.gemini/trustedFolders.json`

), so you
will only be asked once per folder.

When a folder is **untrusted**, the Gemini CLI runs in a restricted "safe mode"
to protect you. In this mode, the following features are disabled:

**Workspace settings are ignored**: The CLI will **not** load the
`.gemini/settings.json`

file from the project. This prevents the loading of
custom tools and other potentially dangerous configurations.

**Environment variables are ignored**: The CLI will **not** load any `.env`

files from the project.

**Extension management is restricted**: You **cannot install, update, or
uninstall** extensions.

**Tool auto-acceptance is disabled**: You will always be prompted before any
tool is run, even if you have auto-acceptance enabled globally.

**Automatic memory loading is disabled**: The CLI will not automatically
load files into context from directories specified in local settings.

**MCP servers do not connect**: The CLI will not attempt to connect to any
Model Context Protocol (MCP) servers.

**Custom commands are not loaded**: The CLI will not load any custom
commands from .toml files, including both project-specific and global user
commands.

Granting trust to a folder unlocks the full functionality of the Gemini CLI for that workspace.

If you need to change a decision or see all your settings, you have a couple of options:

**Change the current folder's trust**: Run the `/permissions`

command from
within the CLI. This will bring up the same interactive dialog, allowing you
to change the trust level for the current folder.

**View all trust rules**: To see a complete list of all your trusted and
untrusted folder rules, you can inspect the contents of the
`~/.gemini/trustedFolders.json`

file in your home directory.

For advanced users, it's helpful to know the exact order of operations for how trust is determined:

**IDE trust signal**: If you are using the
IDE Integration, the CLI first asks the IDE
if the workspace is trusted. The IDE's response takes highest priority.

**Local trust file**: If the IDE is not connected, the CLI checks the
central `~/.gemini/trustedFolders.json`

file.