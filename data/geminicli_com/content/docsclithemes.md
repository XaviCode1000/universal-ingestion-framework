---
url: https://geminicli.com/docs/cli/themes
title: Themes
author: null
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

Gemini CLI supports a variety of themes to customize its color scheme and
appearance. You can change the theme to suit your preferences via the `/theme`

command or `"theme":`

configuration setting.

Gemini CLI comes with a selection of pre-defined themes, which you can list
using the `/theme`

command within Gemini CLI:

`ANSI`

`Atom One`

`Ayu`

`Default`

`Dracula`

`GitHub`

`ANSI Light`

`Ayu Light`

`Default Light`

`GitHub Light`

`Google Code`

`Xcode`

`/theme`

into Gemini CLI.**Note:** If a theme is defined in your `settings.json`

file (either by name or
by a file path), you must remove the `"theme"`

setting from the file before you
can change the theme using the `/theme`

command.

Selected themes are saved in Gemini CLI's configuration so your preference is remembered across sessions.

Gemini CLI allows you to create your own custom color themes by specifying them
in your `settings.json`

file. This gives you full control over the color palette
used in the CLI.

Add a `customThemes`

block to your user, project, or system `settings.json`

file. Each custom theme is defined as an object with a unique name and a set of
color keys. For example:

**Color keys:**

`Background`

`Foreground`

`LightBlue`

`AccentBlue`

`AccentPurple`

`AccentCyan`

`AccentGreen`

`AccentYellow`

`AccentRed`

`Comment`

`Gray`

`DiffAdded`

(optional, for added lines in diffs)`DiffRemoved`

(optional, for removed lines in diffs)`DiffModified`

(optional, for modified lines in diffs)You can also override individual UI text roles by adding a nested `text`

object.
This object supports the keys `primary`

, `secondary`

, `link`

, `accent`

, and
`response`

. When `text.response`

is provided it takes precedence over
`text.primary`

for rendering model responses in chat.

**Required properties:**

`name`

(must match the key in the `customThemes`

object and be a string)`type`

(must be the string `"custom"`

)`Background`

`Foreground`

`LightBlue`

`AccentBlue`

`AccentPurple`

`AccentCyan`

`AccentGreen`

`AccentYellow`

`AccentRed`

`Comment`

`Gray`

You can use either hex codes (e.g., `#FF0000`

) **or** standard CSS color names
(e.g., `coral`

, `teal`

, `blue`

) for any color value. See
CSS color names
for a full list of supported names.

You can define multiple custom themes by adding more entries to the
`customThemes`

object.

In addition to defining custom themes in `settings.json`

, you can also load a
theme directly from a JSON file by specifying the file path in your
`settings.json`

. This is useful for sharing themes or keeping them separate from
your main configuration.

To load a theme from a file, set the `theme`

property in your `settings.json`

to
the path of your theme file:

The theme file must be a valid JSON file that follows the same structure as a
custom theme defined in `settings.json`

.

**Example my-theme.json:**

**Security note:** For your safety, Gemini CLI will only load theme files that
are located within your home directory. If you attempt to load a theme from
outside your home directory, a warning will be displayed and the theme will not
be loaded. This is to prevent loading potentially malicious theme files from
untrusted sources.

`/theme`

command in Gemini CLI. Your custom
theme will appear in the theme selection dialog.`"theme": "MyCustomTheme"`

to the `ui`

object in your `settings.json`

.