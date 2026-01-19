---
url: https://geminicli.com/docs/cli/token-caching
title: Token caching and cost optimization
author: null
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

Gemini CLI automatically optimizes API costs through token caching when using API key authentication (Gemini API key or Vertex AI). This feature reuses previous system instructions and context to reduce the number of tokens processed in subsequent requests.

**Token caching is available for:**

**Token caching is not available for:**

You can view your token usage and cached token savings using the `/stats`

command. When cached tokens are available, they will be displayed in the stats
output.