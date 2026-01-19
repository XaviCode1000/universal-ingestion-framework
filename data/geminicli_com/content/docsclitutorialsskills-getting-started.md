---
url: https://geminicli.com/docs/cli/tutorials/skills-getting-started
title: Getting Started with Agent Skills
author: null
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

Agent Skills allow you to extend Gemini CLI with specialized expertise. This tutorial will guide you through creating your first skill, enabling it, and using it in a session.

Agent Skills are currently an experimental feature and must be enabled in your settings.

`gemini`

.`/settings`

to open the interactive settings dialog.`true`

.`Esc`

to save and exit. You may need to restart the CLI for the
changes to take effect.`settings.json`

Alternatively, you can manually edit your global settings file at
`~/.gemini/settings.json`

(create it if it doesn't exist):

A skill is a directory containing a `SKILL.md`

file. Let's create an **API
Auditor** skill that helps you verify if local or remote endpoints are
responding correctly.

**Create the skill directory structure:**

**Create the SKILL.md file:** Create a file at

`.gemini/skills/api-auditor/SKILL.md`

with the following content:**Create the bundled Node.js script:** Create a file at
`.gemini/skills/api-auditor/scripts/audit.js`

. This script will be used by
the agent to perform the actual check:

Use the `/skills`

slash command (or `gemini skills list`

from your terminal) to
see if Gemini CLI has found your new skill.

In a Gemini CLI session:

You should see `api-auditor`

in the list of available skills.

Now, let's see the skill in action. Start a new session and ask a question about an endpoint.

**User:** "Can you audit http://geminili.com"

Gemini will recognize the request matches the `api-auditor`

description and will
ask for your permission to activate it.

**Model:** (After calling `activate_skill`

) "I've activated the **api-auditor**
skill. I'll run the audit script now…"

Gemini will then use the `run_shell_command`

tool to execute your bundled Node
script:

`node .gemini/skills/api-auditor/scripts/audit.js http://geminili.com`