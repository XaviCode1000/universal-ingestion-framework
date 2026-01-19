---
url: https://geminicli.com/docs/tools/web-search
title: Web search tool (`google_web_search`)
author: null
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

This document describes the `google_web_search`

tool.

Use `google_web_search`

to perform a web search using Google Search via the
Gemini API. The `google_web_search`

tool returns a summary of web results with
sources.

`google_web_search`

takes one argument:

`query`

(string, required): The search query.`google_web_search`

with the Gemini CLIThe `google_web_search`

tool sends a query to the Gemini API, which then
performs a web search. `google_web_search`

will return a generated response
based on the search results, including citations and sources.

Usage:

`google_web_search`

examplesGet information on a topic:

`google_web_search`

tool returns a processed
summary, not a raw list of search results.