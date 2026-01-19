---
url: https://geminicli.com/docs/cli/keyboard-shortcuts
title: Gemini CLI keyboard shortcuts
author: null
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

Gemini CLI ships with a set of default keyboard shortcuts for editing input, navigating history, and controlling the UI. Use this reference to learn the available combinations.

| Action | Keys |
|---|---|
| Confirm the current selection or choice. | `Enter` |
| Dismiss dialogs or cancel the current focus. | `Esc` |
| Cancel the current request or quit the CLI when input is empty. | `Ctrl + C` |
| Exit the CLI when the input buffer is empty. | `Ctrl + D` |

| Action | Keys |
|---|---|
| Move the cursor to the start of the line. | `Ctrl + A` `Home` |
| Move the cursor to the end of the line. | `Ctrl + E` `End` |
| Move the cursor up one line. | `Up Arrow (no Ctrl, no Cmd)` |
| Move the cursor down one line. | `Down Arrow (no Ctrl, no Cmd)` |
| Move the cursor one character to the left. | `Left Arrow (no Ctrl, no Cmd)` `Ctrl + B` |
| Move the cursor one character to the right. | `Right Arrow (no Ctrl, no Cmd)` `Ctrl + F` |
| Move the cursor one word to the left. | `Ctrl + Left Arrow` `Cmd + Left Arrow` `Cmd + B` |
| Move the cursor one word to the right. | `Ctrl + Right Arrow` `Cmd + Right Arrow` `Cmd + F` |

| Action | Keys |
|---|---|
| Delete from the cursor to the end of the line. | `Ctrl + K` |
| Delete from the cursor to the start of the line. | `Ctrl + U` |
| Clear all text in the input field. | `Ctrl + C` |
| Delete the previous word. | `Ctrl + Backspace` `Cmd + Backspace` `Ctrl + W` |
| Delete the next word. | `Ctrl + Delete` `Cmd + Delete` |
| Delete the character to the left. | `Backspace` `Ctrl + H` |
| Delete the character to the right. | `Delete` `Ctrl + D` |
| Undo the most recent text edit. | `Ctrl + Z (no Shift)` |
| Redo the most recent undone text edit. | `Ctrl + Shift + Z` |

| Action | Keys |
|---|---|
| Scroll content up. | `Shift + Up Arrow` |
| Scroll content down. | `Shift + Down Arrow` |
| Scroll to the top. | `Home` |
| Scroll to the bottom. | `End` |
| Scroll up by one page. | `Page Up` |
| Scroll down by one page. | `Page Down` |

| Action | Keys |
|---|---|
| Show the previous entry in history. | `Ctrl + P (no Shift)` |
| Show the next entry in history. | `Ctrl + N (no Shift)` |
| Start reverse search through history. | `Ctrl + R` |
| Submit the selected reverse-search match. | `Enter (no Ctrl)` |
| Accept a suggestion while reverse searching. | `Tab` |

| Action | Keys |
|---|---|
| Move selection up in lists. | `Up Arrow (no Shift)` |
| Move selection down in lists. | `Down Arrow (no Shift)` |
| Move up within dialog options. | `Up Arrow (no Shift)` `K (no Shift)` |
| Move down within dialog options. | `Down Arrow (no Shift)` `J (no Shift)` |

| Action | Keys |
|---|---|
| Accept the inline suggestion. | `Tab` `Enter (no Ctrl)` |
| Move to the previous completion option. | `Up Arrow (no Shift)` `Ctrl + P (no Shift)` |
| Move to the next completion option. | `Down Arrow (no Shift)` `Ctrl + N (no Shift)` |
| Expand an inline suggestion. | `Right Arrow` |
| Collapse an inline suggestion. | `Left Arrow` |

| Action | Keys |
|---|---|
| Submit the current prompt. | `Enter (no Ctrl, no Shift, no Cmd)` |
| Insert a newline without submitting. | `Ctrl + Enter` `Cmd + Enter` `Shift + Enter` `Ctrl + J` |
| Open the current prompt in an external editor. | `Ctrl + X` |
| Paste from the clipboard. | `Ctrl + V` `Cmd + V` |

| Action | Keys |
|---|---|
| Toggle detailed error information. | `F12` |
| Toggle the full TODO list. | `Ctrl + T` |
| Show IDE context details. | `Ctrl + G` |
| Toggle Markdown rendering. | `Cmd + M` |
| Toggle copy mode when in alternate buffer mode. | `Ctrl + S` |
| Toggle YOLO (auto-approval) mode for tool calls. | `Ctrl + Y` |
| Toggle Auto Edit (auto-accept edits) mode. | `Shift + Tab` |
| Expand a height-constrained response to show additional lines when not in alternate buffer mode. | `Ctrl + S` |
| Focus the shell input from the gemini input. | `Tab (no Shift)` |
| Focus the Gemini input from the shell input. | `Tab` |
| Clear the terminal screen and redraw the UI. | `Ctrl + L` |
| Restart the application. | `R` |

`Option+B/F/M`

(macOS only): Are interpreted as `Cmd+B/F/M`

even if your
terminal isn't configured to send Meta with Option.`!`

on an empty prompt: Enter or exit shell mode.`\`

(at end of a line) + `Enter`

: Insert a newline without leaving single-line
mode.`Esc`

pressed twice quickly: Browse and rewind previous interactions.`Up Arrow`

/ `Down Arrow`

: When the cursor is at the top or bottom of a
single-line input, navigate backward or forward through prompt history.`Number keys (1-9, multi-digit)`

inside selection dialogs: Jump directly to
the numbered radio option and confirm when the full number is entered.