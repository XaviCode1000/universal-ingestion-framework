---
url: https://geminicli.com/docs/cli/sandbox
title: Sandboxing in the Gemini CLI
author: null
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

This document provides a guide to sandboxing in the Gemini CLI, including prerequisites, quickstart, and configuration.

Before using sandboxing, you need to install and set up the Gemini CLI:

To verify the installation:

Sandboxing isolates potentially dangerous operations (such as shell commands or file modifications) from your host system, providing a security barrier between AI operations and your environment.

The benefits of sandboxing include:

Your ideal method of sandboxing may differ depending on your platform and your preferred container solution.

Lightweight, built-in sandboxing using `sandbox-exec`

.

**Default profile**: `permissive-open`

- restricts writes outside project
directory but allows most other operations.

Cross-platform sandboxing with complete process isolation.

**Note**: Requires building the sandbox image locally or using a published image
from your organization's registry.

`-s`

or `--sandbox`

`GEMINI_SANDBOX=true|docker|podman|sandbox-exec`

`"sandbox": true`

in the `tools`

object of your
`settings.json`

file (e.g., `{"tools": {"sandbox": true}}`

).Built-in profiles (set via `SEATBELT_PROFILE`

env var):

`permissive-open`

(default): Write restrictions, network allowed`permissive-closed`

: Write restrictions, no network`permissive-proxied`

: Write restrictions, network via proxy`restrictive-open`

: Strict restrictions, network allowed`restrictive-closed`

: Maximum restrictionsFor container-based sandboxing, you can inject custom flags into the `docker`

or
`podman`

command using the `SANDBOX_FLAGS`

environment variable. This is useful
for advanced configurations, such as disabling security features for specific
use cases.

**Example (Podman)**:

To disable SELinux labeling for volume mounts, you can set the following:

Multiple flags can be provided as a space-separated string:

The sandbox automatically handles user permissions on Linux. Override these permissions with:

**"Operation not permitted"**

**Missing commands**

`sandbox.bashrc`

.**Network issues**

**Note:** If you have `DEBUG=true`

in a project's `.env`

file, it won't affect
gemini-cli due to automatic exclusion. Use `.gemini/.env`

files for gemini-cli
specific debug settings.