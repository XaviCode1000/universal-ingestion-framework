---
url: https://geminicli.com/docs/faq
title: Frequently asked questions (FAQ)
author: null
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

This page provides answers to common questions and solutions to frequent problems encountered while using Gemini CLI.

`API error: 429 - Resource exhausted`

?This error indicates that you have exceeded your API request limit. The Gemini API has rate limits to prevent abuse and ensure fair usage.

To resolve this, you can:

`ERR_REQUIRE_ESM`

error when running `npm run start`

?This error typically occurs in Node.js projects when there is a mismatch between CommonJS and ES Modules.

This is often due to a misconfiguration in your `package.json`

or
`tsconfig.json`

. Ensure that:

`package.json`

has `"type": "module"`

.`tsconfig.json`

has `"module": "NodeNext"`

or a compatible setting in
the `compilerOptions`

.If the problem persists, try deleting your `node_modules`

directory and
`package-lock.json`

file, and then run `npm install`

again.

Cached token information is only displayed when cached tokens are being used.
This feature is available for API key users (Gemini API key or Google Cloud
Vertex AI) but not for OAuth users (such as Google Personal/Enterprise accounts
like Google Gmail or Google Workspace, respectively). This is because the Gemini
Code Assist API does not support cached content creation. You can still view
your total token usage using the `/stats`

command in Gemini CLI.

If you installed it globally via `npm`

, update it using the command
`npm install -g @google/gemini-cli@latest`

. If you compiled it from source, pull
the latest changes from the repository, and then rebuild using the command
`npm run build`

.

`chmod +x`

?Commands like `chmod`

are specific to Unix-like operating systems (Linux,
macOS). They are not available on Windows by default.

To resolve this, you can:

`chmod`

, you can use `icacls`

to modify file permissions on Windows.`GOOGLE_CLOUD_PROJECT`

?You can configure your Google Cloud Project ID using an environment variable.

Set the `GOOGLE_CLOUD_PROJECT`

environment variable in your shell:

To make this setting permanent, add this line to your shell's startup file
(e.g., `~/.bashrc`

, `~/.zshrc`

).

Exposing API keys in scripts or checking them into source control is a security risk.

To store your API keys securely, you can:

`.env`

file:`.env`

file in your project's `.gemini`

directory (`.gemini/.env`

) and store your keys there. Gemini CLI will
automatically load these variables.The Gemini CLI configuration is stored in two `settings.json`

files:

`~/.gemini/settings.json`

.`./.gemini/settings.json`

.Refer to Gemini CLI Configuration for more details.

To learn more about your Google AI Pro or Google AI Ultra subscription, visit
**Manage subscription** in your subscription settings.

If you're subscribed to Google AI Pro or Ultra, you automatically have higher limits to Gemini Code Assist and Gemini CLI. These are shared across Gemini CLI and agent mode in the IDE. You can confirm you have higher limits by checking if you are still subscribed to Google AI Pro or Ultra in your subscription settings.

To learn more about your privacy policy and terms of service governed by your subscription, visit Gemini Code Assist: Terms of Service and Privacy Policies.

The higher limits in your Google AI Pro or Ultra subscription are for Gemini 2.5 across both Gemini 2.5 Pro and Flash. They are shared quota across Gemini CLI and agent mode in Gemini Code Assist IDE extensions. You can learn more about quota limits for Gemini CLI, Gemini Code Assist and agent mode in Gemini Code Assist at Quotas and limits.

Google does not use your data to improve Google's machine learning models if you purchase a paid plan. Note: If you decide to remain on the free version of Gemini Code Assist, Gemini Code Assist for individuals, you can also opt out of using your data to improve Google's machine learning models. See the Gemini Code Assist for individuals privacy notice for more information.

Search the Gemini CLI Q&A discussions on GitHub or start a new discussion on GitHub