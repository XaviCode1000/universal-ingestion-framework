---
url: https://geminicli.com/docs/contributing/
title: How to contribute
author: null
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

We would love to accept your patches and contributions to this project. This document includes:

We're looking forward to seeing your contributions!

Contributions to this project must be accompanied by a Contributor License Agreement (CLA). You (or your employer) retain the copyright to your contribution; this simply gives us permission to use and redistribute your contributions as part of the project.

If you or your current employer have already signed the Google CLA (even if it was for a different project), you probably don't need to do it again.

Visit https://cla.developers.google.com/ to see your current agreements or to sign a new one.

This project follows Google's Open Source Community Guidelines.

The process for contributing code is as follows:

`🔒Maintainers only`

, this means it is reserved for project maintainers. We
will not accept pull requests related to these issues. In the near future,
we will explicitly mark issues looking for contributions using the
`help wanted`

label. If you believe an issue is a good candidate for
community contribution, please leave a comment on the issue. A maintainer
will review it and apply the `help-wanted`

label if appropriate. Only
maintainers should attempt to add the `help-wanted`

label to an issue.`packages/`

directory.`npm run preflight`

.All submissions, including submissions by project members, require review. We use GitHub pull requests for this purpose.

If your pull request involves changes to `packages/cli`

(the frontend), we
recommend running our automated frontend review tool. **Note: This tool is
currently experimental.** It helps detect common React anti-patterns, testing
issues, and other frontend-specific best practices that are easy to miss.

To run the review tool, enter the following command from within Gemini CLI:

Replace `<PR_NUMBER>`

with your pull request number. Authors are encouraged to
run this on their own PRs for self-review, and reviewers should use it to
augment their manual review process.

To assign an issue to yourself, simply add a comment with the text `/assign`

.
The comment must contain only that text and nothing else. This command will
assign the issue to you, provided it is not already assigned.

Please note that you can have a maximum of 3 issues assigned to you at any given time.

To help us review and merge your PRs quickly, please follow these guidelines. PRs that do not meet these standards may be closed.

All PRs should be linked to an existing issue in our tracker. This ensures that every change has been discussed and is aligned with the project's goals before any code is written.

If an issue for your change doesn't exist, we will automatically close your PR
along with a comment reminding you to associate the PR with an issue. The ideal
workflow starts with an issue that has been reviewed and approved by a
maintainer. Please **open the issue first** and wait for feedback before you
start coding.

We favor small, atomic PRs that address a single issue or add a single, self-contained feature.

Large changes should be broken down into a series of smaller, logical PRs that can be reviewed and merged independently.

If you'd like to get early feedback on your work, please use GitHub's **Draft
Pull Request** feature. This signals to the maintainers that the PR is not yet
ready for a formal review but is open for discussion and initial feedback.

Before submitting your PR, ensure that all automated checks are passing by
running `npm run preflight`

. This command runs all tests, linting, and other
style checks.

If your PR introduces a user-facing change (e.g., a new command, a modified
flag, or a change in behavior), you must also update the relevant documentation
in the `/docs`

directory.

See more about writing documentation: Documentation contribution process.

Your PR should have a clear, descriptive title and a detailed description of the changes. Follow the Conventional Commits standard for your commit messages.

`feat(cli): Add --json flag to 'config get' command`

`Made some changes`

In the PR description, explain the "why" behind your changes and link to the
relevant issue (e.g., `Fixes #123`

).

If you are forking the repository you will be able to run the Build, Test and
Integration test workflows. However in order to make the integration tests run
you'll need to add a
GitHub Repository Secret
with a value of `GEMINI_API_KEY`

and set that to a valid API key that you have
available. Your key and secret are private to your repo; no one without access
can see your key and you cannot see any secrets related to this repo.

Additionally you will need to click on the `Actions`

tab and enable workflows
for your repository, you'll find it's the large blue button in the center of the
screen.

This section guides contributors on how to build, modify, and understand the development setup of this project.

**Prerequisites:**

`~20.19.0`

. This specific version is
required due to an upstream development dependency issue. You can use a
tool like nvm to manage Node.js versions.`>=20`

is acceptable.To clone the repository:

To install dependencies defined in `package.json`

as well as root dependencies:

To build the entire project (all packages):

This command typically compiles TypeScript to JavaScript, bundles assets, and
prepares the packages for execution. Refer to `scripts/build.js`

and
`package.json`

scripts for more details on what happens during the build.

Sandboxing is highly recommended and requires, at a minimum,
setting `GEMINI_SANDBOX=true`

in your `~/.env`

and ensuring a sandboxing
provider (e.g. `macOS Seatbelt`

, `docker`

, or `podman`

) is available. See
Sandboxing for details.

To build both the `gemini`

CLI utility and the sandbox container, run
`build:all`

from the root directory:

To skip building the sandbox container, you can use `npm run build`

instead.

To start the Gemini CLI from the source code (after building), run the following command from the root directory:

If you'd like to run the source build outside of the gemini-cli folder, you can
utilize `npm link path/to/gemini-cli/packages/cli`

(see:
docs) or
`alias gemini="node path/to/gemini-cli/packages/cli"`

to run with `gemini`

This project contains two types of tests: unit tests and integration tests.

To execute the unit test suite for the project:

This will run tests located in the `packages/core`

and `packages/cli`

directories. Ensure tests pass before submitting any changes. For a more
comprehensive check, it is recommended to run `npm run preflight`

.

The integration tests are designed to validate the end-to-end functionality of
the Gemini CLI. They are not run as part of the default `npm run test`

command.

To run the integration tests, use the following command:

For more detailed information on the integration testing framework, please see the Integration Tests documentation.

To ensure code quality and formatting consistency, run the preflight check:

This command will run ESLint, Prettier, all tests, and other checks as defined
in the project's `package.json`

.

*ProTip*

after cloning create a git precommit hook file to ensure your commits are always clean.

To separately format the code in this project by running the following command from the root directory:

This command uses Prettier to format the code according to the project's style guidelines.

To separately lint the code in this project, run the following command from the root directory:

`packages/`

: Contains the individual sub-packages of the project.
`a2a-server`

: A2A server implementation for the Gemini CLI. (Experimental)`cli/`

: The command-line interface.`core/`

: The core backend logic for the Gemini CLI.`test-utils`

Utilities for creating and cleaning temporary file systems for
testing.`vscode-ide-companion/`

: The Gemini CLI Companion extension pairs with
Gemini CLI.`docs/`

: Contains all project documentation.`scripts/`

: Utility scripts for building, testing, and development tasks.For more detailed architecture, see `docs/architecture.md`

.

`F5`

`node --inspect-brk dist/gemini.js`

within the
`packages/cli`

directory, pausing execution until a debugger attaches. You
can then open `chrome://inspect`

in your Chrome browser to connect to the
debugger.`.vscode/launch.json`

).Alternatively, you can use the "Launch Program" configuration in VS Code if you prefer to launch the currently open file directly, but 'F5' is generally recommended.

To hit a breakpoint inside the sandbox container run:

**Note:** If you have `DEBUG=true`

in a project's `.env`

file, it won't affect
gemini-cli due to automatic exclusion. Use `.gemini/.env`

files for gemini-cli
specific debug settings.

To debug the CLI's React-based UI, you can use React DevTools. Ink, the library used for the CLI's interface, is compatible with React DevTools version 4.x.

**Start the Gemini CLI in development mode:**

**Install and run React DevTools version 4.28.5 (or the latest compatible
4.x version):**

You can either install it globally:

Or run it directly using npx:

Your running CLI application should then connect to React DevTools.

On macOS, `gemini`

uses Seatbelt (`sandbox-exec`

) under a `permissive-open`

profile (see `packages/cli/src/utils/sandbox-macos-permissive-open.sb`

) that
restricts writes to the project folder but otherwise allows all other operations
and outbound network traffic ("open") by default. You can switch to a
`restrictive-closed`

profile (see
`packages/cli/src/utils/sandbox-macos-restrictive-closed.sb`

) that declines all
operations and outbound network traffic ("closed") by default by setting
`SEATBELT_PROFILE=restrictive-closed`

in your environment or `.env`

file.
Available built-in profiles are `{permissive,restrictive}-{open,closed,proxied}`

(see below for proxied networking). You can also switch to a custom profile
`SEATBELT_PROFILE=<profile>`

if you also create a file
`.gemini/sandbox-macos-<profile>.sb`

under your project settings directory
`.gemini`

.

For stronger container-based sandboxing on macOS or other platforms, you can set
`GEMINI_SANDBOX=true|docker|podman|<command>`

in your environment or `.env`

file. The specified command (or if `true`

then either `docker`

or `podman`

) must
be installed on the host machine. Once enabled, `npm run build:all`

will build a
minimal container ("sandbox") image and `npm start`

will launch inside a fresh
instance of that container. The first build can take 20-30s (mostly due to
downloading of the base image) but after that both build and start overhead
should be minimal. Default builds (`npm run build`

) will not rebuild the
sandbox.

Container-based sandboxing mounts the project directory (and system temp
directory) with read-write access and is started/stopped/removed automatically
as you start/stop Gemini CLI. Files created within the sandbox should be
automatically mapped to your user/group on host machine. You can easily specify
additional mounts, ports, or environment variables by setting
`SANDBOX_{MOUNTS,PORTS,ENV}`

as needed. You can also fully customize the sandbox
for your projects by creating the files `.gemini/sandbox.Dockerfile`

and/or
`.gemini/sandbox.bashrc`

under your project settings directory (`.gemini`

) and
running `gemini`

with `BUILD_SANDBOX=1`

to trigger building of your custom
sandbox.

All sandboxing methods, including macOS Seatbelt using `*-proxied`

profiles,
support restricting outbound network traffic through a custom proxy server that
can be specified as `GEMINI_SANDBOX_PROXY_COMMAND=<command>`

, where `<command>`

must start a proxy server that listens on `:::8877`

for relevant requests. See
`docs/examples/proxy-script.md`

for a minimal proxy that only allows `HTTPS`

connections to `example.com:443`

(e.g. `curl https://example.com`

) and declines
all other requests. The proxy is started and stopped automatically alongside the
sandbox.

We publish an artifact for each commit to our internal registry. But if you need to manually cut a local build, then run the following commands:

Our documentation must be kept up-to-date with our code contributions. We want our documentation to be clear, concise, and helpful to our users. We value:

The process for contributing to the documentation is similar to contributing code.

`/docs`

directory.Our documentation is organized using sidebar.json as the table of contents. When adding new documentation:

`/docs`

.`sidebar.json`

in the relevant section.We follow the Google Developer Documentation Style Guide. Please refer to it for guidance on writing style, tone, and formatting.

We use `prettier`

to enforce a consistent style across our documentation. The
`npm run preflight`

command will check for any linting issues.

You can also run the linter and formatter separately:

`npm run lint`

- Check for linting issues`npm run format`

- Auto-format markdown files`npm run lint:fix`

- Auto-fix linting issues where possiblePlease make sure your contributions are free of linting errors before submitting a pull request.

Before submitting your documentation pull request, please:

`npm run preflight`

to ensure all checks pass.If you have questions about contributing documentation:

We appreciate your contributions to making Gemini CLI documentation better!