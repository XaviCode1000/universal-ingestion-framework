---
url: https://geminicli.com/docs/npm
title: Package overview
author: null
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

This monorepo contains two main packages: `@google/gemini-cli`

and
`@google/gemini-cli-core`

.

`@google/gemini-cli`

This is the main package for the Gemini CLI. It is responsible for the user interface, command parsing, and all other user-facing functionality.

When this package is published, it is bundled into a single executable file.
This bundle includes all of the package's dependencies, including
`@google/gemini-cli-core`

. This means that whether a user installs the package
with `npm install -g @google/gemini-cli`

or runs it directly with
`npx @google/gemini-cli`

, they are using this single, self-contained executable.

`@google/gemini-cli-core`

This package contains the core logic for interacting with the Gemini API. It is responsible for making API requests, handling authentication, and managing the local cache.

This package is not bundled. When it is published, it is published as a standard
Node.js package with its own dependencies. This allows it to be used as a
standalone package in other projects, if needed. All transpiled js code in the
`dist`

folder is included in the package.

This project uses NPM Workspaces to manage the packages within this monorepo. This simplifies development by allowing us to manage dependencies and run scripts across multiple packages from the root of the project.

The root `package.json`

file defines the workspaces for this project:

This tells NPM that any folder inside the `packages`

directory is a separate
package that should be managed as part of the workspace.

`npm install`

from the root of
the project will install all dependencies for all packages in the workspace
and link them together. This means you don't need to run `npm install`

in each
package's directory.`npm install`

, NPM will automatically create symlinks between the
packages. This means that when you make changes to one package, the changes
are immediately available to other packages that depend on it.`--workspace`

flag. For example, to run the
`build`

script in the `cli`

package, you can run
`npm run build --workspace @google/gemini-cli`

.