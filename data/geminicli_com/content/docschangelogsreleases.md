---
url: https://geminicli.com/docs/changelogs/releases/
title: Gemini CLI changelog
author: null
date: '2025-11-20'
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

Gemini CLI has three major release channels: nightly, preview, and stable. For most users, we recommend the stable release.

On this page, you can find information regarding the current releases and highlights from each release.

For the full changelog, including nightly releases, refer to Releases - google-gemini/gemini-cli on GitHub.

| Release channel | Notes |
|---|---|
| Nightly | Nightly release with the most recent changes. |
| Preview | Experimental features ready for early feedback. |
| Latest | Stable, recommended for general use. |

`npm install -g @google/gemini-cli@preview`

`/settings`

`/model`

persistence across Gemini CLI sessions by @niyasrad
in https://github.com/google-gemini/gemini-cli/pull/13199`type`

field to MCPServerConfig by @jackwotherspoon in
https://github.com/google-gemini/gemini-cli/pull/15465`/dir add`

command by @jackwotherspoon in
https://github.com/google-gemini/gemini-cli/pull/15724**Full changelog**:
https://github.com/google-gemini/gemini-cli/compare/v0.23.0-preview.6…v0.24.0-preview.0

`npx gemini-wrapped`

to visualize your usage
stats, top models, languages, and more!`Alt`

+`V`

.
(pr by
@sgeraldes)`/logout`

command to instantly clear
credentials and reset your authentication state for seamless account
switching. (pr by
@CN-Scars)`/auth logout`

command to clear credentials and auth state by
@CN-Scars in https://github.com/google-gemini/gemini-cli/pull/13383`GenerateContentConfig`

s and reduce mutation. by
@joshualitt in https://github.com/google-gemini/gemini-cli/pull/14920`.geminiignore`

support to SearchText tool by @xyrolle in
https://github.com/google-gemini/gemini-cli/pull/13763**Full changelog**:
https://github.com/google-gemini/gemini-cli/compare/v0.22.5…v0.23.0

`/auth logout`

command to clear credentials and auth state by
@CN-Scars in https://github.com/google-gemini/gemini-cli/pull/13383`GenerateContentConfig`

s and reduce mutation. by
@joshualitt in https://github.com/google-gemini/gemini-cli/pull/14920`.geminiignore`

support to SearchText tool by @xyrolle in
https://github.com/google-gemini/gemini-cli/pull/13763**Full changelog**:
https://github.com/google-gemini/gemini-cli/compare/v0.22.0-preview.3…v0.23.0-preview.0

`/stats`

command, even those not yet used in your current
session. (pic,
pr by
@sehoon38)`/stats`

view to prioritize
actionable quota information while providing a detailed token and
cache-efficiency breakdown in `/stats model`

(login with Google,
api key,
model stats,
pr by
@jacob314)`@`

.
(pr by
@jackwotherspoon)**Full changelog**:
https://github.com/google-gemini/gemini-cli/compare/v0.21.3…v0.22.0

`/settings`

and set `true`

to enable Gemini 3. For more information:
Gemini 3 Flash is now available in Gemini CLI.`url`

in config by
@jackwotherspoon in https://github.com/google-gemini/gemini-cli/pull/13762`--type`

alias for `--transport`

flag in gemini mcp add by
@jackwotherspoon in https://github.com/google-gemini/gemini-cli/pull/14503`notifications/tools/list_changed`

by @Adib234 in https://github.com/google-gemini/gemini-cli/pull/14375`gemini_cli.startup_stats`

for startup stats. by
@kevin-ramdass in https://github.com/google-gemini/gemini-cli/pull/14734**Full changelog**:
https://github.com/google-gemini/gemini-cli/compare/v0.20.2…v0.21.0

**Full changelog**:
https://github.com/google-gemini/gemini-cli/compare/v0.21.0-preview.6…v0.22.0-preview.0

`/clear`

command to preserve input history for up-arrow navigation while
still clearing the context window and screen by @korade-krushna in
https://github.com/google-gemini/gemini-cli/pull/14182`executor`

. by @joshualitt in
https://github.com/google-gemini/gemini-cli/pull/14305**Full changelog**:
https://github.com/google-gemini/gemini-cli/compare/v0.19.4…v0.20.0

`/settings`

.`/settings`

and enable `BaseLlmClient.generateContent`

. by @joshualitt in
https://github.com/google-gemini/gemini-cli/pull/13591**Full changelog**:
https://github.com/google-gemini/gemini-cli/compare/v0.18.4…v0.19.0

`BaseLlmClient.generateContent`

. by @joshualitt in
https://github.com/google-gemini/gemini-cli/pull/13591**Full changelog**:
https://github.com/google-gemini/gemini-cli/compare/v0.18.0-preview.4…v0.19.0-preview.0

`/settings`

flag and toggling `/settings`

command and setting `true`

.`/settings`

and turn on `gemini extensions uninstall`

.Remove obsolete reference to "help wanted" label in CONTRIBUTING.md by @aswinashok44 in https://github.com/google-gemini/gemini-cli/pull/13291

chore(release): v0.18.0-nightly.20251118.86828bb56 by @skeshive in https://github.com/google-gemini/gemini-cli/pull/13309

Docs: Access clarification. by @jkcinouye in https://github.com/google-gemini/gemini-cli/pull/13304

Fix links in Gemini 3 Pro documentation by @gmackall in https://github.com/google-gemini/gemini-cli/pull/13312

Improve keyboard code parsing by @scidomino in https://github.com/google-gemini/gemini-cli/pull/13307

fix(core): Ensure `read_many_files`

tool is available to zed. by @joshualitt
in https://github.com/google-gemini/gemini-cli/pull/13338

Support 3-parameter modifyOtherKeys sequences by @scidomino in https://github.com/google-gemini/gemini-cli/pull/13342

Improve pty resize error handling for Windows by @galz10 in https://github.com/google-gemini/gemini-cli/pull/13353

fix(ui): Clear input prompt on Escape key press by @SandyTao520 in https://github.com/google-gemini/gemini-cli/pull/13335

bug(ui) showLineNumbers had the wrong default value. by @jacob314 in https://github.com/google-gemini/gemini-cli/pull/13356

fix(cli): fix crash on startup in NO_COLOR mode (#13343) due to ungua… by @avilladsen in https://github.com/google-gemini/gemini-cli/pull/13352

fix: allow MCP prompts with spaces in name by @jackwotherspoon in https://github.com/google-gemini/gemini-cli/pull/12910

Refactor createTransport to duplicate less code by @davidmcwherter in https://github.com/google-gemini/gemini-cli/pull/13010

Followup from #10719 by @bl-ue in https://github.com/google-gemini/gemini-cli/pull/13243

Capturing github action workflow name if present and send it to clearcut by @MJjainam in https://github.com/google-gemini/gemini-cli/pull/13132

feat(sessions): record interactive-only errors and warnings to chat recording JSON files by @bl-ue in https://github.com/google-gemini/gemini-cli/pull/13300

fix(zed-integration): Correctly handle cancellation errors by @benbrandt in https://github.com/google-gemini/gemini-cli/pull/13399

docs: Add Code Wiki link to README by @holtskinner in https://github.com/google-gemini/gemini-cli/pull/13289

Restore keyboard mode when exiting the editor by @scidomino in https://github.com/google-gemini/gemini-cli/pull/13350

feat(core, cli): Bump genai version to 1.30.0 by @joshualitt in https://github.com/google-gemini/gemini-cli/pull/13435

[cli-ui] Keep header ASCII art colored on non-gradient terminals (#13373) by @bniladridas in https://github.com/google-gemini/gemini-cli/pull/13374

Fix Copyright line in LICENSE by @scidomino in https://github.com/google-gemini/gemini-cli/pull/13449

Fix typo in write_todos methodology instructions by @Smetalo in https://github.com/google-gemini/gemini-cli/pull/13411

feat: update thinking mode support to exclude gemini-2.0 models and simplify logic. by @kevin-ramdass in https://github.com/google-gemini/gemini-cli/pull/13454

remove unneeded log by @scidomino in https://github.com/google-gemini/gemini-cli/pull/13456

feat: add click-to-focus support for interactive shell by @galz10 in https://github.com/google-gemini/gemini-cli/pull/13341

Add User email detail to about box by @ptone in https://github.com/google-gemini/gemini-cli/pull/13459

feat(core): Wire up chat code path for model configs. by @joshualitt in https://github.com/google-gemini/gemini-cli/pull/12850

chore/release: bump version to 0.18.0-nightly.20251120.2231497b1 by @gemini-cli-robot in https://github.com/google-gemini/gemini-cli/pull/13476

feat(core): Fix bug with incorrect model overriding. by @joshualitt in https://github.com/google-gemini/gemini-cli/pull/13477

Use synchronous writes when detecting keyboard modes by @scidomino in https://github.com/google-gemini/gemini-cli/pull/13478

fix(cli): prevent race condition when restoring prompt after context overflow by @SandyTao520 in https://github.com/google-gemini/gemini-cli/pull/13473

Revert "feat(core): Fix bug with incorrect model overriding." by @adamfweidman in https://github.com/google-gemini/gemini-cli/pull/13483

Fix: Update system instruction when GEMINI.md memory is loaded or refreshed by @lifefloating in https://github.com/google-gemini/gemini-cli/pull/12136

fix(zed-integration): Ensure that the zed integration is classified as interactive by @benbrandt in https://github.com/google-gemini/gemini-cli/pull/13394

Copy commands as part of setup-github by @gsehgal in https://github.com/google-gemini/gemini-cli/pull/13464

Update banner design by @Adib234 in https://github.com/google-gemini/gemini-cli/pull/13420

Protect stdout and stderr so JavaScript code can't accidentally write to stdout corrupting ink rendering by @jacob314 in https://github.com/google-gemini/gemini-cli/pull/13247

Enable switching preview features on/off without restart by @Adib234 in https://github.com/google-gemini/gemini-cli/pull/13515

feat(core): Use thinking level for Gemini 3 by @joshualitt in https://github.com/google-gemini/gemini-cli/pull/13445

Change default compress threshold to 0.5 for api key users by @scidomino in https://github.com/google-gemini/gemini-cli/pull/13517

remove duplicated mouse code by @scidomino in https://github.com/google-gemini/gemini-cli/pull/13525

feat(zed-integration): Use default model routing for Zed integration by @benbrandt in https://github.com/google-gemini/gemini-cli/pull/13398

feat(core): Incorporate Gemini 3 into model config hierarchy. by @joshualitt in https://github.com/google-gemini/gemini-cli/pull/13447

fix(patch): cherry-pick 5e218a5 to release/v0.18.0-preview.0-pr-13623 to patch version v0.18.0-preview.0 and create version 0.18.0-preview.1 by @gemini-cli-robot in https://github.com/google-gemini/gemini-cli/pull/13626

fix(patch): cherry-pick d351f07 to release/v0.18.0-preview.1-pr-12535 to patch version v0.18.0-preview.1 and create version 0.18.0-preview.2 by @gemini-cli-robot in https://github.com/google-gemini/gemini-cli/pull/13813

fix(patch): cherry-pick 3e50be1 to release/v0.18.0-preview.2-pr-13428 to patch version v0.18.0-preview.2 and create version 0.18.0-preview.3 by @gemini-cli-robot in https://github.com/google-gemini/gemini-cli/pull/13821

fix(patch): cherry-pick d8a3d08 to release/v0.18.0-preview.3-pr-13791 to patch version v0.18.0-preview.3 and create version 0.18.0-preview.4 by @gemini-cli-robot in https://github.com/google-gemini/gemini-cli/pull/13826

**Full changelog**:
https://github.com/google-gemini/gemini-cli/compare/v0.17.1…v0.18.0