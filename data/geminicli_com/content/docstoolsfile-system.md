---
url: https://geminicli.com/docs/tools/file-system
title: Gemini CLI file system tools
author: null
date: '2000-01-01'
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

The Gemini CLI provides a comprehensive suite of tools for interacting with the local file system. These tools allow the Gemini model to read from, write to, list, search, and modify files and directories, all under your control and typically with confirmation for sensitive operations.

**Note:** All file system tools operate within a `rootDirectory`

(usually the
current working directory where you launched the CLI) for security. Paths that
you provide to these tools are generally expected to be absolute or are resolved
relative to this root directory.

`list_directory`

(ReadFolder)`list_directory`

lists the names of files and subdirectories directly within a
specified directory path. It can optionally ignore entries matching provided
glob patterns.

`list_directory`

`ls.ts`

`path`

(string, required): The absolute path to the directory to list.`ignore`

(array of strings, optional): A list of glob patterns to exclude
from the listing (e.g., `["*.log", ".git"]`

).`respect_git_ignore`

(boolean, optional): Whether to respect `.gitignore`

patterns when listing files. Defaults to `true`

.`llmContent`

):`Directory listing for /path/to/your/folder:\n[DIR] subfolder1\nfile1.txt\nfile2.png`

`read_file`

(ReadFile)`read_file`

reads and returns the content of a specified file. This tool handles
text, images (PNG, JPG, GIF, WEBP, SVG, BMP), audio files (MP3, WAV, AIFF, AAC,
OGG, FLAC), and PDF files. For text files, it can read specific line ranges.
Other binary file types are generally skipped.

`read_file`

`read-file.ts`

`path`

(string, required): The absolute path to the file to read.`offset`

(number, optional): For text files, the 0-based line number to
start reading from. Requires `limit`

to be set.`limit`

(number, optional): For text files, the maximum number of lines to
read. If omitted, reads a default maximum (e.g., 2000 lines) or the entire
file if feasible.`offset`

and `limit`

are used,
returns only that slice of lines. Indicates if content was truncated due to
line limits or line length limits.`llmContent`

):
`[File content truncated: showing lines 1-100 of 500 total lines...]\nActual file content...`

).`inlineData`

with `mimeType`

and base64 `data`

(e.g.,
`{ inlineData: { mimeType: 'image/png', data: 'base64encodedstring' } }`

).`Cannot display content of binary file: /path/to/data.bin`

.`write_file`

(WriteFile)`write_file`

writes content to a specified file. If the file exists, it will be
overwritten. If the file doesn't exist, it (and any necessary parent
directories) will be created.

`write_file`

`write-file.ts`

`file_path`

(string, required): The absolute path to the file to write to.`content`

(string, required): The content to write into the file.`content`

to the `file_path`

.`llmContent`

):`Successfully overwrote file: /path/to/your/file.txt`

or
`Successfully created and wrote to new file: /path/to/new/file.txt`

.`glob`

(FindFiles)`glob`

finds files matching specific glob patterns (e.g., `src/**/*.ts`

,
`*.md`

), returning absolute paths sorted by modification time (newest first).

`glob`

`glob.ts`

`pattern`

(string, required): The glob pattern to match against (e.g.,
`"*.py"`

, `"src/**/*.js"`

).`path`

(string, optional): The absolute path to the directory to search
within. If omitted, searches the tool's root directory.`case_sensitive`

(boolean, optional): Whether the search should be
case-sensitive. Defaults to `false`

.`respect_git_ignore`

(boolean, optional): Whether to respect .gitignore
patterns when finding files. Defaults to `true`

.`node_modules`

and `.git`

by
default.`llmContent`

):`Found 5 file(s) matching "*.ts" within src, sorted by modification time (newest first):\nsrc/file1.ts\nsrc/subdir/file2.ts...`

`search_file_content`

(SearchText)`search_file_content`

searches for a regular expression pattern within the
content of files in a specified directory. Can filter files by a glob pattern.
Returns the lines containing matches, along with their file paths and line
numbers.

`search_file_content`

`grep.ts`

`pattern`

(string, required): The regular expression (regex) to search for
(e.g., `"function\s+myFunction"`

).`path`

(string, optional): The absolute path to the directory to search
within. Defaults to the current working directory.`include`

(string, optional): A glob pattern to filter which files are
searched (e.g., `"*.js"`

, `"src/**/*.{ts,tsx}"`

). If omitted, searches most
files (respecting common ignores).`git grep`

if available in a Git repository for speed; otherwise, falls
back to system `grep`

or a JavaScript-based search.`llmContent`

):`replace`

(Edit)`replace`

replaces text within a file. By default, replaces a single occurrence,
but can replace multiple occurrences when `expected_replacements`

is specified.
This tool is designed for precise, targeted changes and requires significant
context around the `old_string`

to ensure it modifies the correct location.

**Tool name:** `replace`

**Display name:** Edit

**File:** `edit.ts`

**Parameters:**

`file_path`

(string, required): The absolute path to the file to modify.

`old_string`

(string, required): The exact literal text to replace.

**CRITICAL:** This string must uniquely identify the single instance to
change. It should include at least 3 lines of context *before* and *after*
the target text, matching whitespace and indentation precisely. If
`old_string`

is empty, the tool attempts to create a new file at `file_path`

with `new_string`

as content.

`new_string`

(string, required): The exact literal text to replace
`old_string`

with.

`expected_replacements`

(number, optional): The number of occurrences to
replace. Defaults to `1`

.

**Behavior:**

`old_string`

is empty and `file_path`

does not exist, creates a new file
with `new_string`

as content.`old_string`

is provided, it reads the `file_path`

and attempts to find
exactly one occurrence of `old_string`

.`new_string`

.`old_string`

might not be perfectly precise, the tool incorporates a
multi-stage edit correction mechanism.
`old_string`

isn't found or matches multiple locations, the
tool can leverage the Gemini model to iteratively refine `old_string`

(and
potentially `new_string`

).`replace`

operation more robust even
with slightly imperfect initial context.**Failure conditions:** Despite the correction mechanism, the tool will fail
if:

`file_path`

is not absolute or is outside the root directory.`old_string`

is not empty, but the `file_path`

does not exist.`old_string`

is empty, but the `file_path`

already exists.`old_string`

is not found in the file after attempts to correct it.`old_string`

is found multiple times, and the self-correction mechanism
cannot resolve it to a single, unambiguous match.**Output ( llmContent):**

`Successfully modified file: /path/to/file.txt (1 replacements).`

or
`Created new file: /path/to/new_file.txt with provided content.`

`Failed to edit, 0 occurrences found...`

,
`Failed to edit, expected 1 occurrences but found 2...`

).**Confirmation:** Yes. Shows a diff of the proposed changes and asks for user
approval before writing to the file.

These file system tools provide a foundation for the Gemini CLI to understand and interact with your local project context.