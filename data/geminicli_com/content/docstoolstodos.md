---
url: https://geminicli.com/docs/tools/todos
title: Todo tool (`write_todos`)
author: null
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

This document describes the `write_todos`

tool for the Gemini CLI.

The `write_todos`

tool allows the Gemini agent to create and manage a list of
subtasks for complex user requests. This provides you, the user, with greater
visibility into the agent's plan and its current progress. It also helps with
alignment where the agent is less likely to lose track of its current goal.

`write_todos`

takes one argument:

`todos`

(array of objects, required): The complete list of todo items. This
replaces the existing list. Each item includes:
`description`

(string): The task description.`status`

(string): The current status (`pending`

, `in_progress`

,
`completed`

, or `cancelled`

).The agent uses this tool to break down complex multi-step requests into a clear plan.

`completed`

when done.`in_progress`

at a time,
indicating exactly what the agent is currently working on.When active, the current `in_progress`

task is displayed above the input box,
keeping you informed of the immediate action. You can toggle the full view of
the todo list at any time by pressing `Ctrl+T`

.

Usage example (internal representation):

**Enabling:** This tool is enabled by default. You can disable it in your
`settings.json`

file by setting `"useWriteTodos": false`

.

**Intended use:** This tool is primarily used by the agent for complex,
multi-turn tasks. It is generally not used for simple, single-turn questions.