---
url: https://geminicli.com/docs/cli/gemini-md
title: Provide context with GEMINI.md files
author: null
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

Context files, which use the default name `GEMINI.md`

, are a powerful feature
for providing instructional context to the Gemini model. You can use these files
to give project-specific instructions, define a persona, or provide coding style
guides to make the AI's responses more accurate and tailored to your needs.

Instead of repeating instructions in every prompt, you can define them once in a context file.

The CLI uses a hierarchical system to source context. It loads various context files from several locations, concatenates the contents of all found files, and sends them to the model with every prompt. The CLI loads files in the following order:

**Global context file:**

`~/.gemini/GEMINI.md`

(in your user home directory).**Project root and ancestor context files:**

`GEMINI.md`

file in your current
working directory and then in each parent directory up to the project root
(identified by a `.git`

folder).**Sub-directory context files:**

`GEMINI.md`

files in subdirectories
below your current working directory. It respects rules in `.gitignore`

and `.geminiignore`

.The CLI footer displays the number of loaded context files, which gives you a quick visual cue of the active instructional context.

`GEMINI.md`

fileHere is an example of what you can include in a `GEMINI.md`

file at the root of
a TypeScript project:

`/memory`

commandYou can interact with the loaded context files by using the `/memory`

command.

`/memory show`

`/memory refresh`

`GEMINI.md`

files
from all configured locations.`/memory add <text>`

`~/.gemini/GEMINI.md`

file. This lets you add persistent memories on the fly.You can break down large `GEMINI.md`

files into smaller, more manageable
components by importing content from other files using the `@file.md`

syntax.
This feature supports both relative and absolute paths.

**Example GEMINI.md with imports:**

For more details, see the Memory Import Processor documentation.

While `GEMINI.md`

is the default filename, you can configure this in your
`settings.json`

file. To specify a different name or a list of names, use the
`context.fileName`

property.

**Example settings.json:**