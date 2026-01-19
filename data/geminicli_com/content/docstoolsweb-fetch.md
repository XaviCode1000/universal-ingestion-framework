---
url: https://geminicli.com/docs/tools/web-fetch
title: Web fetch tool (`web_fetch`)
author: null
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

This document describes the `web_fetch`

tool for the Gemini CLI.

Use `web_fetch`

to summarize, compare, or extract information from web pages.
The `web_fetch`

tool processes content from one or more URLs (up to 20) embedded
in a prompt. `web_fetch`

takes a natural language prompt and returns a generated
response.

`web_fetch`

takes one argument:

`prompt`

(string, required): A comprehensive prompt that includes the URL(s)
(up to 20) to fetch and specific instructions on how to process their content.
For example:
`"Summarize https://example.com/article and extract key points from https://another.com/data"`

.
The prompt must contain at least one URL starting with `http://`

or
`https://`

.`web_fetch`

with the Gemini CLITo use `web_fetch`

with the Gemini CLI, provide a natural language prompt that
contains URLs. The tool will ask for confirmation before fetching any URLs. Once
confirmed, the tool will process URLs through Gemini API's `urlContext`

.

If the Gemini API cannot access the URL, the tool will fall back to fetching content directly from the local machine. The tool will format the response, including source attribution and citations where possible. The tool will then provide the response to the user.

Usage:

`web_fetch`

examplesSummarize a single article:

Compare two articles:

`web_fetch`

relies on the Gemini API's ability to access
and process the given URLs.