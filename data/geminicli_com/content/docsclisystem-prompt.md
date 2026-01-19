---
url: https://geminicli.com/docs/cli/system-prompt
title: System Prompt Override (GEMINI_SYSTEM_MD)
author: null
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

The core system instructions that guide Gemini CLI can be completely replaced
with your own Markdown file. This feature is controlled via the
`GEMINI_SYSTEM_MD`

environment variable.

The `GEMINI_SYSTEM_MD`

variable instructs the CLI to use an external Markdown
file for its system prompt, completely overriding the built-in default. This is
a full replacement, not a merge. If you use a custom file, none of the original
core instructions will apply unless you include them yourself.

This feature is intended for advanced users who need to enforce strict, project-specific behavior or create a customized persona.

Tip: You can export the current default system prompt to a file first, review it, and then selectively modify or replace it (see "Export the default prompt").

You can set the environment variable temporarily in your shell, or persist it
via a `.gemini/.env`

file. See
Persisting Environment Variables.

Use the project default path (`.gemini/system.md`

):

`GEMINI_SYSTEM_MD=true`

or `GEMINI_SYSTEM_MD=1`

`./.gemini/system.md`

(relative to your current project
directory).Use a custom file path:

`GEMINI_SYSTEM_MD=/absolute/path/to/my-system.md`

`~/my-system.md`

).Disable the override (use built‑in prompt):

`GEMINI_SYSTEM_MD=false`

or `GEMINI_SYSTEM_MD=0`

or unset the variable.If the override is enabled but the target file does not exist, the CLI will
error with: `missing system prompt file '<path>'`

.

`GEMINI_SYSTEM_MD=1 gemini`

`.gemini/.env`

:
`.gemini/system.md`

, then add to `.gemini/.env`

:
`GEMINI_SYSTEM_MD=1`

`GEMINI_SYSTEM_MD=~/prompts/SYSTEM.md gemini`

When `GEMINI_SYSTEM_MD`

is active, the CLI shows a `|⌐■_■|`

indicator in the UI
to signal custom system‑prompt mode.

Before overriding, export the current default prompt so you can review required safety and workflow rules.

`GEMINI_WRITE_SYSTEM_MD=1 gemini`

`GEMINI_WRITE_SYSTEM_MD=~/prompts/DEFAULT_SYSTEM.md gemini`

This creates the file and writes the current built‑in system prompt to it.

Keep SYSTEM.md minimal but complete for safety and tool operation. Keep GEMINI.md focused on high‑level guidance and project specifics.

`missing system prompt file '…'`

`GEMINI_SYSTEM_MD=1|true`

, create `./.gemini/system.md`

in your project.`.gemini/.env`

or export in your shell).`GEMINI_SYSTEM_MD`

or set it to `0`

/`false`

.