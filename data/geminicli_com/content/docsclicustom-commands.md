---
url: https://geminicli.com/docs/cli/custom-commands
title: Custom commands
author: null
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

Custom commands let you save and reuse your favorite or most frequently used prompts as personal shortcuts within Gemini CLI. You can create commands that are specific to a single project or commands that are available globally across all your projects, streamlining your workflow and ensuring consistency.

Gemini CLI discovers commands from two locations, loaded in a specific order:

`~/.gemini/commands/`

. These commands
are available in any project you are working on.`<your-project-root>/.gemini/commands/`

. These commands are specific to the
current project and can be checked into version control to be shared with
your team.If a command in the project directory has the same name as a command in the user
directory, the **project command will always be used.** This allows projects to
override global commands with project-specific versions.

The name of a command is determined by its file path relative to its `commands`

directory. Subdirectories are used to create namespaced commands, with the path
separator (`/`

or `\`

) being converted to a colon (`:`

).

`~/.gemini/commands/test.toml`

becomes the command `/test`

.`<project>/.gemini/commands/git/commit.toml`

becomes the namespaced
command `/git:commit`

.Your command definition files must be written in the TOML format and use the
`.toml`

file extension.

`prompt`

(String): The prompt that will be sent to the Gemini model when the
command is executed. This can be a single-line or multi-line string.`description`

(String): A brief, one-line description of what the command
does. This text will be displayed next to your command in the `/help`

menu.
Custom commands support two powerful methods for handling arguments. The CLI
automatically chooses the correct method based on the content of your command's
`prompt`

.

`{{args}}`

If your `prompt`

contains the special placeholder `{{args}}`

, the CLI will
replace that placeholder with the text the user typed after the command name.

The behavior of this injection depends on where it is used:

**A. Raw injection (outside shell commands)**

When used in the main body of the prompt, the arguments are injected exactly as the user typed them.

**Example ( git/fix.toml):**

The model receives:
`Please provide a code fix for the issue described here: "Button is misaligned".`

**B. Using arguments in shell commands (inside !{...} blocks)**

When you use `{{args}}`

inside a shell injection block (`!{...}`

), the arguments
are automatically **shell-escaped** before replacement. This allows you to
safely pass arguments to shell commands, ensuring the resulting command is
syntactically correct and secure while preventing command injection
vulnerabilities.

**Example ( /grep-code.toml):**

When you run `/grep-code It's complicated`

:

`{{args}}`

used both outside and inside `!{...}`

.`{{args}}`

is replaced raw with `It's complicated`

.`{{args}}`

is replaced with the escaped version (e.g., on
Linux: `"It\'s complicated"`

).`grep -r "It's complicated" .`

.If your `prompt`

does **not** contain the special placeholder `{{args}}`

, the
CLI uses a default behavior for handling arguments.

If you provide arguments to the command (e.g., `/mycommand arg1`

), the CLI will
append the full command you typed to the end of the prompt, separated by two
newlines. This allows the model to see both the original instructions and the
specific arguments you just provided.

If you do **not** provide any arguments (e.g., `/mycommand`

), the prompt is sent
to the model exactly as it is, with nothing appended.

**Example ( changelog.toml):**

This example shows how to create a robust command by defining a role for the model, explaining where to find the user's input, and specifying the expected format and behavior.

When you run `/changelog 1.2.0 added "New feature"`

, the final text sent to the
model will be the original prompt followed by two newlines and the command you
typed.

`!{...}`

You can make your commands dynamic by executing shell commands directly within
your `prompt`

and injecting their output. This is ideal for gathering context
from your local environment, like reading file content or checking the status of
Git.

When a custom command attempts to execute a shell command, Gemini CLI will now prompt you for confirmation before proceeding. This is a security measure to ensure that only intended commands can be run.

**How it works:**

`!{...}`

syntax.`{{args}}`

is present inside the block, it is
automatically shell-escaped (see
Context-Aware Injection above).`!{...}`

must have balanced braces (`{`

and `}`

). If you need to execute a
command containing unbalanced braces, consider wrapping it in an external
script file and calling the script within the `!{...}`

block.`[Shell command exited with code 1]`

. This helps the model understand the
context of the failure.**Example ( git/commit.toml):**

This command gets the staged git diff and uses it to ask the model to write a commit message.

When you run `/git:commit`

, the CLI first executes `git diff --staged`

, then
replaces `!{git diff --staged}`

with the output of that command before sending
the final, complete prompt to the model.

`@{...}`

You can directly embed the content of a file or a directory listing into your
prompt using the `@{...}`

syntax. This is useful for creating commands that
operate on specific files.

**How it works:**

`@{path/to/file.txt}`

is replaced by the content of
`file.txt`

.`@{path/to/dir}`

is traversed and each file present
within the directory and all subdirectories is inserted into the prompt. This
respects `.gitignore`

and `.geminiignore`

if enabled.`@{...}`

is processed
`!{...}`

) and argument substitution (`{{args}}`

).`@{...}`

(the path) to
have balanced braces (`{`

and `}`

).**Example ( review.toml):**

This command injects the content of a *fixed* best practices file
(`docs/best-practices.md`

) and uses the user's arguments to provide context for
the review.

When you run `/review FileCommandLoader.ts`

, the `@{docs/best-practices.md}`

placeholder is replaced by the content of that file, and `{{args}}`

is replaced
by the text you provided, before the final prompt is sent to the model.

Let's create a global command that asks the model to refactor a piece of code.

**1. Create the file and directories:**

First, ensure the user commands directory exists, then create a `refactor`

subdirectory for organization and the final TOML file.

**2. Add the content to the file:**

Open `~/.gemini/commands/refactor/pure.toml`

in your editor and add the
following content. We are including the optional `description`

for best
practice.

**3. Run the command:**

That's it! You can now run your command in the CLI. First, you might add a file to the context, and then invoke your command:

Gemini CLI will then execute the multi-line prompt defined in your TOML file.