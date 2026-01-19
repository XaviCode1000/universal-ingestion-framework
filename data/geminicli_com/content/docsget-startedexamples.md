---
url: https://geminicli.com/docs/get-started/examples
title: Gemini CLI examples
author: null
date: '2023-01-01'
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

Not sure where to get started with Gemini CLI? This document covers examples on how to use Gemini CLI for a variety of tasks.

**Note:** Results are examples intended to showcase potential use cases. Your
results may vary.

Scenario: You have a folder containing the following files:

Give Gemini the following prompt:

Result: Gemini will ask for permission to rename your files.

Select **Allow once** and your files will be renamed:

Scenario: You want to understand how a popular open-source utility works by inspecting its code, not just its README.

Give Gemini CLI the following prompt:

Result: Gemini will perform a sequence of actions to answer your request.

`git clone`

to download the
repository.Gemini CLI will return an explanation based on the actual source code:

Scenario: You have two .csv files: `Revenue - 2023.csv`

and
`Revenue - 2024.csv`

. Each file contains monthly revenue figures, like so:

You want to combine these two .csv files into a single .csv file.

Give Gemini CLI the following prompt:

Result: Gemini CLI will read each file and then ask for permission to write a new file. Provide your permission and Gemini CLI will provide the following .csv:

Scenario: You've written a simple login page. You wish to write unit tests to ensure that your login page has code coverage.

Give Gemini CLI the following prompt:

Result: Gemini CLI will ask for permission to write a new file and create a test for your login page