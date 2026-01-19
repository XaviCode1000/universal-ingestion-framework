---
url: https://geminicli.com/docs/cli/skills
title: Agent Skills
author: null
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

Note: This is an experimental feature enabled via experimental.skills. You
can also search for "Skills" within the /settings interactive UI to toggle
this and manage other skill-related settings.

Agent Skills allow you to extend Gemini CLI with specialized expertise,
procedural workflows, and task-specific resources. Based on the
Agent Skills open standard, a "skill" is a
self-contained directory that packages instructions and assets into a
discoverable capability.

Unlike general context files (GEMINI.md), which provide
persistent workspace-wide background, Skills represent on-demand expertise.
This allows Gemini to maintain a vast library of specialized capabilities—such
as security auditing, cloud deployments, or codebase migrations—without
cluttering the model's immediate context window.

Gemini autonomously decides when to employ a skill based on your request and the
skill's description. When a relevant skill is identified, the model "pulls in"
the full instructions and resources required to complete the task using the
activate_skill tool.

Shared Expertise: Package complex workflows (like a specific team's PR
review process) into a folder that anyone can use.

Repeatable Workflows: Ensure complex multi-step tasks are performed
consistently by providing a procedural framework.

Resource Bundling: Include scripts, templates, or example data alongside
instructions so the agent has everything it needs.

Progressive Disclosure: Only skill metadata (name and description) is
loaded initially. Detailed instructions and resources are only disclosed when
the model explicitly activates the skill, saving context tokens.

While you can structure your skill directory however you like, the Agent Skills
standard encourages these conventions:

scripts/: Executable scripts (bash, python, node) the agent can run.

references/: Static documentation, schemas, or example data for the
agent to consult.

assets/: Code templates, boilerplate, or binary resources.

When a skill is activated, Gemini CLI provides the model with a tree view of the
entire skill directory, allowing it to discover and utilize these assets.

Discovery: At the start of a session, Gemini CLI scans the discovery
tiers and injects the name and description of all enabled skills into the
system prompt.

Activation: When Gemini identifies a task matching a skill's
description, it calls the activate_skill tool.

Consent: You will see a confirmation prompt in the UI detailing the
skill's name, purpose, and the directory path it will gain access to.

Injection: Upon your approval:

The SKILL.md body and folder structure is added to the conversation
history.

The skill's directory is added to the agent's allowed file paths, granting
it permission to read any bundled assets.

Execution: The model proceeds with the specialized expertise active. It
is instructed to prioritize the skill's procedural guidance within reason.

This website uses cookies from Google to deliver and enhance the quality of its services and to analyze
traffic.