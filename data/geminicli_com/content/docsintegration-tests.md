---
url: https://geminicli.com/docs/integration-tests
title: Integration tests
author: null
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

This document provides information about the integration testing framework used in this project.

The integration tests are designed to validate the end-to-end functionality of the Gemini CLI. They execute the built binary in a controlled environment and verify that it behaves as expected when interacting with the file system.

These tests are located in the `integration-tests`

directory and are run using a
custom test runner.

Prior to running any integration tests, you need to create a release bundle that you want to actually test:

You must re-run this command after making any changes to the CLI source code, but not after making changes to tests.

The integration tests are not run as part of the default `npm run test`

command.
They must be run explicitly using the `npm run test:integration:all`

script.

The integration tests can also be run using the following shortcut:

To run a subset of test files, you can use
`npm run <integration test command> <file_name1> ....`

where <integration
test command> is either `test:e2e`

or `test:integration*`

and `<file_name>`

is any of the `.test.js`

files in the `integration-tests/`

directory. For
example, the following command runs `list_directory.test.js`

and
`write_file.test.js`

:

To run a single test by its name, use the `--test-name-pattern`

flag:

Some integration tests use faked out model responses, which may need to be regenerated from time to time as the implementations change.

To regenerate these golden files, set the REGENERATE_MODEL_GOLDENS environment variable to "true" when running the tests, for example:

**WARNING**: If running locally you should review these updated responses for
any information about yourself or your system that gemini may have included in
these responses.

**WARNING**: Make sure you run **await rig.cleanup()** at the end of your test,
else the golden files will not be updated.

Before adding a **new** integration test, you should test it at least 5 times
with the deflake script or workflow to make sure that it is not flaky.

To run the entire suite of integration tests, use the following command:

The `all`

command will run tests for `no sandboxing`

, `docker`

and `podman`

.
Each individual type can be run using the following commands:

The integration test runner provides several options for diagnostics to help track down test failures.

You can preserve the temporary files created during a test run for inspection. This is useful for debugging issues with file system operations.

To keep the test output set the `KEEP_OUTPUT`

environment variable to `true`

.

When output is kept, the test runner will print the path to the unique directory for the test run.

For more detailed debugging, set the `VERBOSE`

environment variable to `true`

.

When using `VERBOSE=true`

and `KEEP_OUTPUT=true`

in the same command, the output
is streamed to the console and also saved to a log file within the test's
temporary directory.

The verbose output is formatted to clearly identify the source of the logs:

To ensure code quality and consistency, the integration test files are linted as part of the main build process. You can also manually run the linter and auto-fixer.

To check for linting errors, run the following command:

You can include the `:fix`

flag in the command to automatically fix any fixable
linting errors:

The integration tests create a unique directory for each test run inside the
`.integration-tests`

directory. Within this directory, a subdirectory is created
for each test file, and within that, a subdirectory is created for each
individual test case.

This structure makes it easy to locate the artifacts for a specific test run, file, or case.

To ensure the integration tests are always run, a GitHub Actions workflow is
defined in `.github/workflows/chained_e2e.yml`

. This workflow automatically runs
the integrations tests for pull requests against the `main`

branch, or when a
pull request is added to a merge queue.

The workflow runs the tests in different sandboxing environments to ensure Gemini CLI is tested across each:

`sandbox:none`

: Runs the tests without any sandboxing.`sandbox:docker`

: Runs the tests in a Docker container.`sandbox:podman`

: Runs the tests in a Podman container.