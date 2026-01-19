---
url: https://geminicli.com/docs/releases
title: Gemini CLI releases
author: null
date: '2000-01-01'
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

`dev`

vs `prod`

environmentOur release flows support both `dev`

and `prod`

environments.

The `dev`

environment pushes to a private Github-hosted NPM repository, with the
package names beginning with `@google-gemini/**`

instead of `@google/**`

.

The `prod`

environment pushes to the public global NPM registry via Wombat
Dressing Room, which is Google's system for managing NPM packages in the
`@google/**`

namespace. The packages are all named `@google/**`

.

More information can be found about these systems in the NPM Package Overview

| Package | `prod` (Wombat Dressing Room) | `dev` (Github Private NPM Repo) |
|---|---|---|
| CLI | @google/gemini-cli | @google-gemini/gemini-cli |
| Core | @google/gemini-cli-core | @google-gemini/gemini-cli-core A2A Server |
| A2A Server | @google/gemini-cli-a2a-server | @google-gemini/gemini-cli-a2a-server |

We will follow https://semver.org/ as closely as possible but will call out when or if we have to deviate from it. Our weekly releases will be minor version increments and any bug or hotfixes between releases will go out as patch versions on the most recent release.

Each Tuesday ~2000 UTC new Stable and Preview releases will be cut. The promotion flow is:

`preview`

channel`preview`

channel is promoted to `stable`

channel`preview`

and `stable`

as needed,
with the final 'patch' version number incrementing each time.These releases will not have been fully vetted and may contain regressions or
other outstanding issues. Please help us test and install with `preview`

tag.

This will be the full promotion of last week's release + any bug fixes and
validations. Use `latest`

tag.

`nightly`

tag.Each Tuesday, the on-call engineer will trigger the "Promote Release" workflow. This single action automates the entire weekly release process:

`preview`

release and promotes it to `stable`

. This becomes the new `latest`

version
on npm.`nightly`

release is then
promoted to become the new `preview`

version.`main`

in preparation for the next nightly
release.This process ensures a consistent and reliable release cadence with minimal manual intervention.

To ensure the highest reliability, the release promotion process uses the **NPM
registry as the single source of truth** for determining the current version of
each release channel (`stable`

, `preview`

, and `nightly`

).

`dist-tags`

(`latest`

, `preview`

, `nightly`

) to get the exact version strings for the
packages currently available to users.This NPM-first approach, backed by integrity checks, makes the release process highly robust and prevents the kinds of versioning discrepancies that can arise from relying solely on git history or API outputs.

For situations requiring a release outside of the regular nightly and weekly
promotion schedule, and NOT already covered by patching process, you can use the
`Release: Manual`

workflow. This workflow provides a direct way to publish a
specific version from any branch, tag, or commit SHA.

`v0.6.1`

). This must be a
valid semantic version with a `v`

prefix.`preview`

,
`nightly`

, `latest`

(for stable releases), and `dev`

. The default is
`dev`

.`true`

to run all steps without publishing, or set
to `false`

to perform a live release.`true`

to skip the test suite. This is not
recommended for production releases.`true`

to skip creating a GitHub release
and create an npm release only.`dev`

environment
is intended for testing. The `prod`

environment is intended for production
releases. `prod`

is the default and will require authorization from a
release administrator.The workflow will then proceed to test (if not skipped), build, and publish the release. If the workflow fails during a non-dry run, it will automatically create a GitHub issue with the failure details.

In the event that a release has a critical regression, you can quickly roll back
to a previous stable version or roll forward to a new patch by changing the npm
`dist-tag`

. The `Release: Change Tags`

workflow provides a safe and controlled
way to do this.

This is the preferred method for both rollbacks and rollforwards, as it does not require a full release cycle.

`0.5.0-preview-2`

). This version `dist-tag`

to apply (e.g., `preview`

, `stable`

).`true`

to log the action without making changes, or
set to `false`

to perform the live tag change.`dev`

environment
is intended for testing. The `prod`

environment is intended for production
releases. `prod`

is the default and will require authorization from a
release administrator.The workflow will then run `npm dist-tag add`

for the appropriate `gemini-cli`

,
`gemini-cli-core`

and `gemini-cli-a2a-server`

packages, pointing the specified
channel to the specified version.

If a critical bug that is already fixed on `main`

needs to be patched on a
`stable`

or `preview`

release, the process is now highly automated.

There are two ways to create a patch pull request:

**Option A: From a GitHub comment (recommended)**

After a pull request containing the fix has been merged, a maintainer can add a comment on that same PR with the following format:

`/patch [channel]`

`both`

- patches both stable and preview channels (same as default)`stable`

- patches only the stable channel`preview`

- patches only the preview channelExamples:

`/patch`

(patches both stable and preview - default)`/patch both`

(patches both stable and preview - explicit)`/patch stable`

(patches only stable)`/patch preview`

(patches only preview)The `Release: Patch from Comment`

workflow will automatically find the merge
commit SHA and trigger the `Release: Patch (1) Create PR`

workflow. If the PR is
not yet merged, it will post a comment indicating the failure.

**Option B: Manually triggering the workflow**

Navigate to the **Actions** tab and run the **Release: Patch (1) Create PR**
workflow.

`main`

that you want to cherry-pick.`stable`

or `preview`

).This workflow will automatically:

`release/v0.5.1-pr-12345`

).Review the automatically created pull request(s) to ensure the cherry-pick was successful and the changes are correct. Once approved, merge the pull request.

**Security note:** The `release/*`

branches are protected by branch protection
rules. A pull request to one of these branches requires at least one review from
a code owner before it can be merged. This ensures that no unauthorized code is
released.

If you need to include multiple fixes in a single patch release, you can add additional commits to the hotfix branch after the initial patch PR has been created:

**Start with the primary fix**: Use `/patch`

(or `/patch both`

) on the most
important PR to create the initial hotfix branch and PR.

**Checkout the hotfix branch locally**:

**Cherry-pick additional commits**:

**Push the updated branch**:

**Test and review**: The existing patch PR will automatically update with
your additional commits. Test thoroughly since you're now releasing multiple
changes together.

**Update the PR description**: Consider updating the PR title and description
to reflect that it includes multiple fixes.

This approach allows you to group related fixes into a single patch release while maintaining full control over what gets included and how conflicts are resolved.

Upon merging the pull request, the `Release: Patch (2) Trigger`

workflow is
automatically triggered. It will then start the `Release: Patch (3) Release`

workflow, which will:

This fully automated process ensures that patches are created and released consistently and reliably.

**Issue**: If the patch trigger workflow fails with errors like "Resource not
accessible by integration" or references to non-existent workflow files (e.g.,
`patch-release.yml`

), this indicates the hotfix branch contains an outdated
version of the workflow files.

**Root cause**: When a PR is merged, GitHub Actions runs the workflow definition
from the **source branch** (the hotfix branch), not from the target branch (the
release branch). If the hotfix branch was created from an older release branch
that predates workflow improvements, it will use the old workflow logic.

**Solutions**:

**Option 1: Manual trigger (quick fix)** Manually trigger the updated workflow
from the branch with the latest workflow code:

**Note**: Replace `<branch-with-updated-workflow>`

with the branch containing
the latest workflow improvements (usually `main`

, but could be a feature branch
if testing updates).

**Option 2: Update the hotfix branch** Merge the latest main branch into your
hotfix branch to get the updated workflows:

Then close and reopen the PR to retrigger the workflow with the updated version.

**Option 3: Direct release trigger** Skip the trigger workflow entirely and
directly run the release workflow:

We also run a Google cloud build called release-docker.yml. Which publishes the sandbox docker to match your release. This will also be moved to GH and combined with the main release file once service account permissions are sorted out.

After pushing a new release smoke testing should be performed to ensure that the packages are working as expected. This can be done by installing the packages locally and running a set of tests to ensure that they are functioning correctly.

`npx -y @google/gemini-cli@latest --version`

to validate the push worked as
expected if you were not doing a rc or dev tag`npx -y @google/gemini-cli@<release tag> --version`

to validate the tag pushed
appropriately`npm uninstall @google/gemini-cli && npm uninstall -g @google/gemini-cli && npm cache clean --force && npm install @google/gemini-cli@<version>`

If you need to test the release process without actually publishing to NPM or creating a public GitHub release, you can trigger the workflow manually from the GitHub UI.

`dry_run`

option checked (`true`

).This will run the entire release process but will skip the `npm publish`

and
`gh release create`

steps. You can inspect the workflow logs to ensure
everything is working as expected.

It is crucial to test any changes to the packaging and publishing process locally before committing them. This ensures that the packages will be published correctly and that they will work as expected when installed by a user.

To validate your changes, you can perform a dry run of the publishing process. This will simulate the publishing process without actually publishing the packages to the npm registry.

This command will do the following:

You can then inspect the generated tarballs to ensure that they contain the
correct files and that the `package.json`

files have been updated correctly. The
tarballs will be created in the root of each package's directory (e.g.,
`packages/cli/google-gemini-cli-0.1.6.tgz`

).

By performing a dry run, you can be confident that your changes to the packaging process are correct and that the packages will be published successfully.

The release process creates two distinct types of artifacts for different distribution channels: standard packages for the NPM registry and a single, self-contained executable for GitHub Releases.

Here are the key stages:

**Stage 1: Pre-release sanity checks and versioning**

`npm run preflight`

). The version number in the root `package.json`

and
`packages/cli/package.json`

is updated to the new release version.**Stage 2: Building the source code for NPM**

`packages/core/src`

and
`packages/cli/src`

is compiled into standard JavaScript.`packages/core/src/**/*.ts`

-> compiled to -> `packages/core/dist/`

`packages/cli/src/**/*.ts`

-> compiled to -> `packages/cli/dist/`

`core`

package is built
first as the `cli`

package depends on it.**Stage 3: Publishing standard packages to NPM**

`npm publish`

command is run for the
`@google/gemini-cli-core`

and `@google/gemini-cli`

packages.`npm install -g @google/gemini-cli`

will download these packages, and
`npm`

will handle installing the `@google/gemini-cli-core`

dependency
automatically. The code in these packages is not bundled into a single file.**Stage 4: Assembling and creating the GitHub release asset**

This stage happens *after* the NPM publish and creates the single-file
executable that enables `npx`

usage directly from the GitHub repository.

**The JavaScript bundle is created:**

`packages/core/dist`

and
`packages/cli/dist`

, along with all third-party JavaScript dependencies,
are bundled by `esbuild`

into a single, executable JavaScript file (e.g.,
`gemini.js`

). The `node-pty`

library is excluded from this bundle as it
contains native binaries.`npm install`

, as all dependencies (including
the `core`

package) are included directly.**The bundle directory is assembled:**

`bundle`

folder is created at the project
root. The single `gemini.js`

executable is placed inside it, along with
other essential files.`gemini.js`

(from esbuild) -> `bundle/gemini.js`

`README.md`

-> `bundle/README.md`

`LICENSE`

-> `bundle/LICENSE`

`packages/cli/src/utils/*.sb`

(sandbox profiles) -> `bundle/`

**The GitHub release is created:**

`bundle`

directory, including the
`gemini.js`

executable, are attached as assets to a new GitHub Release.`npx https://github.com/google-gemini/gemini-cli`

command, which downloads
and runs this specific bundled asset.**Summary of artifacts**

`packages/cli/dist`

, which depends on
`@google/gemini-cli-core`

.`gemini.js`

file that contains
all dependencies, for easy execution via `npx`

.This dual-artifact process ensures that both traditional `npm`

users and those
who prefer the convenience of `npx`

have an optimized experience.

Failing release workflows will automatically create an issue with the label
`release-failure`

.

A notification will be posted to the maintainer's chat channel when issues with this type are created.

Notifications use
GitHub for Google Chat.
To modify the notifications, use `/github-settings`

within the chat space.

[!WARNING] The following instructions describe a fragile workaround that depends on the internal structure of the chat application's UI. It is likely to break with future updates.

The list of available labels is not currently populated correctly. If you want to add a label that does not appear alphabetically in the first 30 labels in the repo, you must use your browser's developer tools to manually modify the UI:

`/github-settings`

dialog, inspect the list of labels.`<li>`

elements representing a label.`data-option-value`

attribute of that `<li>`

element
to the desired label name (e.g., `release-failure`

).