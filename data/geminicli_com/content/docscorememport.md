---
url: https://geminicli.com/docs/core/memport
title: Memory Import Processor
author: null
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

The Memory Import Processor is a feature that allows you to modularize your
GEMINI.md files by importing content from other files using the `@file.md`

syntax.

This feature enables you to break down large GEMINI.md files into smaller, more manageable components that can be reused across different contexts. The import processor supports both relative and absolute paths, with built-in safety features to prevent circular imports and ensure file access security.

Use the `@`

symbol followed by the path to the file you want to import:

`@./file.md`

- Import from the same directory`@../file.md`

- Import from parent directory`@./components/file.md`

- Import from subdirectory`@/absolute/path/to/file.md`

- Import using absolute pathThe imported files can themselves contain imports, creating a nested structure:

The processor automatically detects and prevents circular imports:

The `validateImportPath`

function ensures that imports are only allowed from
specified directories, preventing access to sensitive files outside the allowed
scope.

To prevent infinite recursion, there's a configurable maximum import depth (default: 5 levels).

If a referenced file doesn't exist, the import will fail gracefully with an error comment in the output.

Permission issues or other file system errors are handled gracefully with appropriate error messages.

The import processor uses the `marked`

library to detect code blocks and inline
code spans, ensuring that `@`

imports inside these regions are properly ignored.
This provides robust handling of nested code blocks and complex Markdown
structures.

The processor returns an import tree that shows the hierarchy of imported files,
similar to Claude's `/memory`

feature. This helps users debug problems with
their GEMINI.md files by showing which files were read and their import
relationships.

Example tree structure:

The tree preserves the order that files were imported and shows the complete import chain for debugging purposes.

`/memory`

(`claude.md`

) approachClaude Code's `/memory`

feature (as seen in `claude.md`

) produces a flat, linear
document by concatenating all included files, always marking file boundaries
with clear comments and path names. It does not explicitly present the import
hierarchy, but the LLM receives all file contents and paths, which is sufficient
for reconstructing the hierarchy if needed.

[!NOTE] The import tree is mainly for clarity during development and has limited relevance to LLM consumption.

`processImports(content, basePath, debugMode?, importState?)`

Processes import statements in GEMINI.md content.

**Parameters:**

`content`

(string): The content to process for imports`basePath`

(string): The directory path where the current file is located`debugMode`

(boolean, optional): Whether to enable debug logging (default:
false)`importState`

(ImportState, optional): State tracking for circular import
prevention**Returns:** Promise<ProcessImportsResult> - Object containing processed
content and import tree

`ProcessImportsResult`

`MemoryFile`

`validateImportPath(importPath, basePath, allowedDirectories)`

Validates import paths to ensure they are safe and within allowed directories.

**Parameters:**

`importPath`

(string): The import path to validate`basePath`

(string): The base directory for resolving relative paths`allowedDirectories`

(string[]): Array of allowed directory paths**Returns:** boolean - Whether the import path is valid

`findProjectRoot(startDir)`

Finds the project root by searching for a `.git`

directory upwards from the
given start directory. Implemented as an **async** function using non-blocking
file system APIs to avoid blocking the Node.js event loop.

**Parameters:**

`startDir`

(string): The directory to start searching from**Returns:** Promise<string> - The project root directory (or the start
directory if no `.git`

is found)

Enable debug mode to see detailed logging of the import process: