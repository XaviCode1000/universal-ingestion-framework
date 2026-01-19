---
url: https://geminicli.com/docs/cli/gemini-ignore
title: Ignoring files
author: null
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

This document provides an overview of the Gemini Ignore (`.geminiignore`

)
feature of the Gemini CLI.

The Gemini CLI includes the ability to automatically ignore files, similar to
`.gitignore`

(used by Git) and `.aiexclude`

(used by Gemini Code Assist). Adding
paths to your `.geminiignore`

file will exclude them from tools that support
this feature, although they will still be visible to other services (such as
Git).

When you add a path to your `.geminiignore`

file, tools that respect this file
will exclude matching files and directories from their operations. For example,
when you use the `@`

command to share files, any paths in your `.geminiignore`

file will be automatically excluded.

For the most part, `.geminiignore`

follows the conventions of `.gitignore`

files:

`#`

are ignored.`*`

, `?`

, and `[]`

).`/`

at the end will only match directories.`/`

at the beginning anchors the path relative to the
`.geminiignore`

file.`!`

negates a pattern.You can update your `.geminiignore`

file at any time. To apply the changes, you
must restart your Gemini CLI session.

`.geminiignore`

To enable `.geminiignore`

:

`.geminiignore`

in the root of your project directory.To add a file or directory to `.geminiignore`

:

`.geminiignore`

file.`/archive/`

or
`apikeys.txt`

.`.geminiignore`

examplesYou can use `.geminiignore`

to ignore directories and files:

You can use wildcards in your `.geminiignore`

file with `*`

:

Finally, you can exclude files and directories from exclusion with `!`

:

To remove paths from your `.geminiignore`

file, delete the relevant lines.