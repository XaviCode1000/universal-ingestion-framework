---
url: https://geminicli.com/docs/troubleshooting
title: Troubleshooting guide
author: null
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

This guide provides solutions to common issues and debugging tips, including topics on:

**Error:
You must be a named user on your organization's Gemini Code Assist Standard edition subscription to use this service. Please contact your administrator to request an entitlement to Gemini Code Assist Standard edition.**

**Cause:** This error might occur if Gemini CLI detects the
`GOOGLE_CLOUD_PROJECT`

or `GOOGLE_CLOUD_PROJECT_ID`

environment variable is
defined. Setting these variables forces an organization subscription check.
This might be an issue if you are using an individual Google account not
linked to an organizational subscription.

**Solution:**

**Individual Users:** Unset the `GOOGLE_CLOUD_PROJECT`

and
`GOOGLE_CLOUD_PROJECT_ID`

environment variables. Check and remove these
variables from your shell configuration files (for example, `.bashrc`

,
`.zshrc`

) and any `.env`

files. If this doesn't resolve the issue, try
using a different Google account.

**Organizational Users:** Contact your Google Cloud administrator to be
added to your organization's Gemini Code Assist subscription.

**Error:
Failed to login. Message: Your current account is not eligible... because it is not currently available in your location.**

**Error: Failed to login. Message: Request contains an invalid argument**

`GOOGLE_CLOUD_PROJECT`

to your project ID. Alternatively, you can obtain the
Gemini API key from
Google AI Studio, which also
includes a separate free tier.**Error: UNABLE_TO_GET_ISSUER_CERT_LOCALLY or
unable to get local issuer certificate**

`NODE_USE_SYSTEM_CA`

; if that does not
resolve the issue, set `NODE_EXTRA_CA_CERTS`

.
`NODE_USE_SYSTEM_CA=1`

environment variable to tell Node.js to use
the operating system's native certificate store (where corporate
certificates are typically already installed).
`export NODE_USE_SYSTEM_CA=1`

`NODE_EXTRA_CA_CERTS`

environment variable to the absolute path of
your corporate root CA certificate file.
`export NODE_EXTRA_CA_CERTS=/path/to/your/corporate-ca.crt`

**Error: EADDRINUSE (Address already in use) when starting an MCP server.**

**Error: Command not found (when attempting to run Gemini CLI with
gemini).**

`PATH`

.`gemini`

globally, check that your `npm`

global binary
directory is in your `PATH`

. You can update Gemini CLI using the command
`npm install -g @google/gemini-cli@latest`

.`gemini`

from source, ensure you are using the correct
command to invoke it (e.g., `node packages/cli/dist/index.js ...`

). To
update Gemini CLI, pull the latest changes from the repository, and then
rebuild using the command `npm run build`

.**Error: MODULE_NOT_FOUND or import errors.**

`npm install`

to ensure all dependencies are present.`npm run build`

to compile the project.`npm run start`

.**Error: "Operation not permitted", "Permission denied", or similar.**

**Gemini CLI is not running in interactive mode in "CI" environments**

`CI_`

(e.g., `CI_TOKEN`

)
is set. This is because the `is-in-ci`

package, used by the underlying UI
framework, detects these variables and assumes a non-interactive CI
environment.`is-in-ci`

package checks for the presence of `CI`

,
`CONTINUOUS_INTEGRATION`

, or any environment variable with a `CI_`

prefix.
When any of these are found, it signals that the environment is
non-interactive, which prevents the Gemini CLI from starting in its
interactive mode.`CI_`

prefixed variable is not needed for the CLI to
function, you can temporarily unset it for the command. e.g.,
`env -u CI_TOKEN gemini`

**DEBUG mode not working from project .env file**

`DEBUG=true`

in a project's `.env`

file doesn't enable
debug mode for gemini-cli.`DEBUG`

and `DEBUG_MODE`

variables are automatically excluded
from project `.env`

files to prevent interference with gemini-cli behavior.`.gemini/.env`

file instead, or configure the
`advanced.excludedEnvVars`

setting in your `settings.json`

to exclude fewer
variables.The Gemini CLI uses specific exit codes to indicate the reason for termination. This is especially useful for scripting and automation.

| Exit Code | Error Type | Description |
|---|---|---|
| 41 | `FatalAuthenticationError` | An error occurred during the authentication process. |
| 42 | `FatalInputError` | Invalid or missing input was provided to the CLI. (non-interactive mode only) |
| 44 | `FatalSandboxError` | An error occurred with the sandboxing environment (e.g., Docker, Podman, or Seatbelt). |
| 52 | `FatalConfigError` | A configuration file (`settings.json` ) is invalid or contains errors. |
| 53 | `FatalTurnLimitedError` | The maximum number of conversational turns for the session was reached. (non-interactive mode only) |

**CLI debugging:**

`--debug`

flag for more detailed output. In interactive mode, press
F12 to view the debug console.**Core debugging:**

`DEBUG_MODE`

environment variable to `true`

or `1`

.`node --inspect`

) if you need to step
through server-side code.**Tool issues:**

`run_shell_command`

, check that the command works directly in your shell
first.**Pre-flight checks:**

`npm run preflight`

before committing code. This can catch many
common issues related to formatting, linting, and type errors.If you encounter an issue that was not covered here in this *Troubleshooting
guide*, consider searching the Gemini CLI
Issue tracker on GitHub.
If you can't find an issue similar to yours, consider creating a new GitHub
Issue with a detailed description. Pull requests are also welcome!

Note:Issues tagged as "🔒Maintainers only" are reserved for project maintainers. We will not accept pull requests related to these issues.