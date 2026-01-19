---
url: https://geminicli.com/docs/core/policy-engine
title: Policy engine
author: null
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

The Gemini CLI includes a powerful policy engine that provides fine-grained control over tool execution. It allows users and administrators to define rules that determine whether a tool call should be allowed, denied, or require user confirmation.

To create your first policy:

`~/.gemini/policies/my-rules.toml`

). You
can use any filename ending in `.toml`

; all such files in this directory
will be loaded and combined:
`git status`

). The tool will now execute automatically without prompting for
confirmation.The policy engine operates on a set of rules. Each rule is a combination of conditions and a resulting decision. When a large language model wants to execute a tool, the policy engine evaluates all rules to find the highest-priority rule that matches the tool call.

A rule consists of the following main components:

`allow`

, `deny`

, or
`ask_user`

).For example, this rule will ask for user confirmation before executing any `git`

command.

Conditions are the criteria that a tool call must meet for a rule to apply. The primary conditions are the tool's name and its arguments.

The `toolName`

in the rule must match the name of the tool being called.

`toolName`

of `my-server__*`

will match any tool from the
`my-server`

MCP.If `argsPattern`

is specified, the tool's arguments are converted to a stable
JSON string, which is then tested against the provided regular expression. If
the arguments don't match the pattern, the rule does not apply.

There are three possible decisions a rule can enforce:

`allow`

: The tool call is executed automatically without user interaction.`deny`

: The tool call is blocked and is not executed.`ask_user`

: The user is prompted to approve or deny the tool call. (In
non-interactive mode, this is treated as `deny`

.)The policy engine uses a sophisticated priority system to resolve conflicts when
multiple rules match a single tool call. The core principle is simple: **the
rule with the highest priority wins**.

To provide a clear hierarchy, policies are organized into three tiers. Each tier has a designated number that forms the base of the final priority calculation.

| Tier | Base | Description |
|---|---|---|
| Default | 1 | Built-in policies that ship with the Gemini CLI. |
| User | 2 | Custom policies defined by the user. |
| Admin | 3 | Policies managed by an administrator (e.g., in an enterprise environment). |

Within a TOML policy file, you assign a priority value from **0 to 999**. The
engine transforms this into a final priority using the following formula:

`final_priority = tier_base + (toml_priority / 1000)`

This system guarantees that:

For example:

`priority: 50`

rule in a Default policy file becomes `1.050`

.`priority: 100`

rule in a User policy file becomes `2.100`

.`priority: 20`

rule in an Admin policy file becomes `3.020`

.Approval modes allow the policy engine to apply different sets of rules based on
the CLI's operational mode. A rule can be associated with one or more modes
(e.g., `yolo`

, `autoEdit`

). The rule will only be active if the CLI is running
in one of its specified modes. If a rule has no modes specified, it is always
active.

When a tool call is made, the engine checks it against all active rules, starting from the highest priority. The first rule that matches determines the outcome.

A rule matches a tool call if all of its conditions are met:

`toolName`

in the rule must match the name of the tool
being called.
`toolName`

of `my-server__*`

will match any tool from the
`my-server`

MCP.`argsPattern`

is specified, the tool's arguments
are converted to a stable JSON string, which is then tested against the
provided regular expression. If the arguments don't match the pattern, the
rule does not apply.Policies are defined in `.toml`

files. The CLI loads these files from Default,
User, and (if configured) Admin directories.

Here is a breakdown of the fields available in a TOML policy rule:

To apply the same rule to multiple tools or command prefixes, you can provide an
array of strings for the `toolName`

and `commandPrefix`

fields.

**Example:**

This single rule will apply to both the `write_file`

and `replace`

tools.

`run_shell_command`

To simplify writing policies for `run_shell_command`

, you can use
`commandPrefix`

or `commandRegex`

instead of the more complex `argsPattern`

.

`commandPrefix`

: Matches if the `command`

argument starts with the given
string.`commandRegex`

: Matches if the `command`

argument matches the given regular
expression.**Example:**

This rule will ask for user confirmation before executing any `git`

command.

You can create rules that target tools from Model-hosting-protocol (MCP) servers
using the `mcpName`

field or a wildcard pattern.

**1. Using mcpName**

To target a specific tool from a specific server, combine `mcpName`

and
`toolName`

.

**2. Using a wildcard**

To create a rule that applies to *all* tools on a specific MCP server, specify
only the `mcpName`

.

The Gemini CLI ships with a set of default policies to provide a safe out-of-the-box experience.

`read_file`

, `glob`

) are generally `delegate_to_agent`

) defaults to `ask_user`

`write_file`

, `run_shell_command`

) default to
`ask_user`

`yolo`

`autoEdit`