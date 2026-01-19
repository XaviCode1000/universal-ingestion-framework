---
url: https://geminicli.com/docs/get-started/gemini-3
title: Gemini 3 Pro and Gemini 3 Flash on Gemini CLI
author: null
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

Gemini 3 Pro and Gemini 3 Flash are available on Gemini CLI for all users!

Get started by upgrading Gemini CLI to the latest version:

After you've confirmed your version is 0.21.1 or later:

`/settings`

command in Gemini CLI.`true`

.`/model`

and select For more information, see Gemini CLI model selection.

Gemini CLI will tell you when you reach your Gemini 3 Pro daily usage limit. When you encounter that limit, you'll be given the option to switch to Gemini 2.5 Pro, upgrade for higher limits, or stop. You'll also be told when your usage limit resets and Gemini 3 Pro can be used again.

Similarly, when you reach your daily usage limit for Gemini 2.5 Pro, you'll see a message prompting fallback to Gemini 2.5 Flash.

There may be times when the Gemini 3 Pro model is overloaded. When that happens, Gemini CLI will ask you to decide whether you want to keep trying Gemini 3 Pro or fallback to Gemini 2.5 Pro.

Note:TheKeep tryingoption uses exponential backoff, in which Gemini CLI waits longer between each retry, when the system is busy. If the retry doesn't happen immediately, please wait a few minutes for the request to process.

When using Gemini CLI, you may want to control how your requests are routed
between models. By default, Gemini CLI uses **Auto** routing.

When using Gemini 3 Pro, you may want to use Auto routing or Pro routing to manage your usage limits:

`/model`

and select To learn more about selecting a model and routing, refer to Gemini CLI Model Selection.

If you're using Gemini Code Assist Standard or Gemini Code Assist Enterprise, enabling Gemini 3 Pro on Gemini CLI requires configuring your release channels. Using Gemini 3 Pro will require two steps: administrative enablement and user enablement.

To learn more about these settings, refer to Configure Gemini Code Assist release channels.

An administrator with **Google Cloud Settings Admin** permissions must follow
these directions:

Wait for two to three minutes after your administrator has enabled **Preview**,
then:

`/settings`

command.`true`

.Restart Gemini CLI and you should have access to Gemini 3.

If you need help, we recommend searching for an existing GitHub issue. If you cannot find a GitHub issue that matches your concern, you can create a new issue. For comments and feedback, consider opening a GitHub discussion.