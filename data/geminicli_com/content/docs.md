---
url: https://geminicli.com/docs
title: Welcome to Gemini CLI documentation
author: null
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

This documentation provides a comprehensive guide to installing, using, and
developing Gemini CLI, a tool that lets you interact with Gemini models through
a command-line interface.

Gemini CLI brings the capabilities of Gemini models to your terminal in an
interactive Read-Eval-Print Loop (REPL) environment. Gemini CLI consists of a
client-side application (`packages/cli`

) that communicates with a local server
(`packages/core`

), which in turn manages requests to the Gemini API and its AI
models. Gemini CLI also contains a variety of tools for tasks such as performing
file system operations, running shells, and web fetching, which are managed by
`packages/core`

.

This documentation is organized into the following sections:

**Architecture overview:** Understand the high-level
design of Gemini CLI, including its components and how they interact.
**Contribution guide:** Information for contributors and
developers, including setup, building, testing, and coding conventions.

**Introduction: Gemini CLI:** Overview of the command-line
interface.
**Commands:** Description of available CLI commands.
**Checkpointing:** Documentation for the
checkpointing feature.
**Custom commands:** Create your own commands and
shortcuts for frequently used prompts.
**Enterprise:** Gemini CLI for enterprise.
**Headless mode:** Use Gemini CLI programmatically for
scripting and automation.
**Keyboard shortcuts:** A reference for all
keyboard shortcuts to improve your workflow.
**Model selection:** Select the model used to process your
commands with `/model`

.
**Sandbox:** Isolate tool execution in a secure,
containerized environment.
**Agent Skills:** (Experimental) Extend the CLI with
specialized expertise and procedural workflows.
**Settings:** Configure various aspects of the CLI's
behavior and appearance with `/settings`

.
**Telemetry:** Overview of telemetry in the CLI.
**Themes:** Themes for Gemini CLI.
**Token caching:** Token caching and optimization.
**Trusted Folders:** An overview of the Trusted
Folders security feature.
**Tutorials:** Tutorials for Gemini CLI.
**Uninstall:** Methods for uninstalling the Gemini CLI.

**Hooks:** Intercept and customize Gemini CLI behavior at
key lifecycle points.
**Writing Hooks:** Learn how to create your first
hook with a comprehensive example.
**Best Practices:** Security, performance, and
debugging guidelines for hooks.

**NPM:** Details on how the project's packages are structured.
**Releases:** Information on the project's releases and
deployment cadence.
**Changelog:** Highlights and notable changes to
Gemini CLI.
**Integration tests:** Information about the
integration testing framework used in this project.
**Issue and PR automation:** A detailed
overview of the automated processes we use to manage and triage issues and
pull requests.

We hope this documentation helps you make the most of Gemini CLI!