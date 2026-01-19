---
url: https://geminicli.com/docs/get-started/installation
title: Gemini CLI installation, execution, and deployment
author: null
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

Install and run Gemini CLI. This document provides an overview of Gemini CLI's installation methods and deployment architecture.

There are several ways to run Gemini CLI. The recommended option depends on how you intend to use Gemini CLI.

This is the recommended way for end-users to install Gemini CLI. It involves downloading the Gemini CLI package from the NPM registry.

**Global install:**

Then, run the CLI from anywhere:

**NPX execution:**

For security and isolation, Gemini CLI can be run inside a container. This is the default way that the CLI executes tools that might have side effects.

`--sandbox`

flag:Contributors to the project will want to run the CLI directly from the source code.

**Development mode:** This method provides hot-reloading and is useful for
active development.

**Production-like mode (linked package):** This method simulates a global
installation by linking your local package. It's useful for testing a local
build in a production workflow.

You can run the most recently committed version of Gemini CLI directly from the GitHub repository. This is useful for testing features still in development.

The execution methods described above are made possible by the following architectural components and processes:

**NPM packages**

Gemini CLI project is a monorepo that publishes two core packages to the NPM registry:

`@google/gemini-cli-core`

: The backend, handling logic and tool execution.`@google/gemini-cli`

: The user-facing frontend.These packages are used when performing the standard installation and when running Gemini CLI from the source.

**Build and packaging processes**

There are two distinct build processes used, depending on the distribution channel:

**NPM publication:** For publishing to the NPM registry, the TypeScript source
code in `@google/gemini-cli-core`

and `@google/gemini-cli`

is transpiled into
standard JavaScript using the TypeScript Compiler (`tsc`

). The resulting
`dist/`

directory is what gets published in the NPM package. This is a
standard approach for TypeScript libraries.

**GitHub npx execution:** When running the latest version of Gemini CLI
directly from GitHub, a different process is triggered by the

`prepare`

script
in `package.json`

. This script uses `esbuild`

to bundle the entire application
and its dependencies into a single, self-contained JavaScript file. This
bundle is created on-the-fly on the user's machine and is not checked into the
repository.**Docker sandbox image**

The Docker-based execution method is supported by the `gemini-cli-sandbox`

container image. This image is published to a container registry and contains a
pre-installed, global version of Gemini CLI.

The release process is automated through GitHub Actions. The release workflow performs the following actions:

`tsc`

.