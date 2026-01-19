---
url: https://geminicli.com/docs/tools/memory
title: Memory tool (`save_memory`)
author: null
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

This document describes the `save_memory`

tool for the Gemini CLI.

Use `save_memory`

to save and recall information across your Gemini CLI
sessions. With `save_memory`

, you can direct the CLI to remember key details
across sessions, providing personalized and directed assistance.

`save_memory`

takes one argument:

`fact`

(string, required): The specific fact or piece of information to
remember. This should be a clear, self-contained statement written in natural
language.`save_memory`

with the Gemini CLIThe tool appends the provided `fact`

to a special `GEMINI.md`

file located in
the user's home directory (`~/.gemini/GEMINI.md`

). This file can be configured
to have a different name.

Once added, the facts are stored under a `## Gemini Added Memories`

section.
This file is loaded as context in subsequent sessions, allowing the CLI to
recall the saved information.

Usage:

`save_memory`

examplesRemember a user preference:

Store a project-specific detail: