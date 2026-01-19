---
url: https://geminicli.com/docs/hooks/best-practices
title: 'Hooks on Gemini CLI: Best practices'
author: Authoring Secure Hooks
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

This guide covers security considerations, performance optimization, debugging
techniques, and privacy considerations for developing and deploying hooks in
Gemini CLI.

Hooks run synchronously—slow hooks delay the agent loop. Optimize for speed by
using parallel operations:

// Sequential operations are slower

const data1 = await fetch (url1). then (( r ) => r. json ());

const data2 = await fetch (url2). then (( r ) => r. json ());

const data3 = await fetch (url3). then (( r ) => r. json ());

// Prefer parallel operations for better performance

// Start requests concurrently

const p1 = fetch (url1). then (( r ) => r. json ());

const p2 = fetch (url2). then (( r ) => r. json ());

const p3 = fetch (url3). then (( r ) => r. json ());

const [ data1 , data2 , data3 ] = await Promise . all ([p1, p2, p3]);

Store results between invocations to avoid repeated computation:

const fs = require ( 'fs' );

const path = require ( 'path' );

const CACHE_FILE = '.gemini/hook-cache.json' ;

return JSON . parse (fs. readFileSync ( CACHE_FILE , 'utf8' ));

function writeCache ( data ) {

fs. writeFileSync ( CACHE_FILE , JSON . stringify (data, null , 2 ));

const cache = readCache ();

const cacheKey = `tool-list-${ ( Date . now () / 3600000 ) | 0 }` ; // Hourly cache

console. log ( JSON . stringify (cache[cacheKey]));

const result = await computeExpensiveResult ();

cache[cacheKey] = result;

console. log ( JSON . stringify (result));

Choose hook events that match your use case to avoid unnecessary execution.
`AfterAgent`

fires once per agent loop completion, while `AfterModel`

fires
after every LLM call (potentially multiple times per loop):

// If checking final completion, use AfterAgent instead of AfterModel

"command" : "./check-completion.sh"

Use specific matchers to avoid unnecessary hook execution. Instead of matching
all tools with `*`

, specify only the tools you need:

"matcher" : "write_file|replace" ,

"name" : "validate-writes" ,

"command" : "./validate.sh"

For large inputs, use streaming JSON parsers to avoid loading everything into
memory:

// Standard approach: parse entire input

const input = JSON . parse ( await readStdin ());

const content = input.tool_input.content;

// For very large inputs: stream and extract only needed fields

const { createReadStream } = require ( 'fs' );

const JSONStream = require ( 'JSONStream' );

const stream = createReadStream ( 0 ). pipe (JSONStream. parse ( 'tool_input.content' ));

stream. on ( 'data' , ( chunk ) => {

Write debug information to dedicated log files:

LOG_FILE = ".gemini/hooks/debug.log"

echo "[$( date '+%Y-%m-%d %H:%M:%S')] $* " >> " $LOG_FILE "

log "Received input: ${ input : 0 : 100 }..."

log "Hook completed successfully"

Error messages on stderr are surfaced appropriately based on exit codes:

const result = dangerousOperation ();

console. log ( JSON . stringify ({ result }));

console. error ( `Hook error: ${ error . message }` );

process. exit ( 2 ); // Blocking error

Run hook scripts manually with sample JSON input:

Terminal window cat > test-input.json << 'EOF'

"session_id": "test-123",

"hook_event_name": "BeforeTool",

"tool_name": "write_file",

"content": "Test content"

cat test-input.json | .gemini/hooks/my-hook.sh

Ensure your script returns the correct exit code:

Hook execution is logged when `telemetry.logPrompts`

is enabled:

View hook telemetry in logs to debug execution issues.

The `/hooks panel`

command shows execution status and recent output:

Check for:

Hook execution counts
Recent successes/failures
Error messages
Execution timing
Begin with basic logging hooks before implementing complex logic:

# Simple logging hook to understand input structure

echo " $input " >> .gemini/hook-inputs.log

Parse JSON with proper libraries instead of text processing:

Bad:

Terminal window tool_name = $( echo " $input " | grep -oP '"tool_name":\s*"\K[^"]+' )

Good:

Terminal window tool_name = $( echo " $input " | jq -r '.tool_name' )

Always make hook scripts executable:

Terminal window chmod +x .gemini/hooks/ * .sh

chmod +x .gemini/hooks/ * .js

Commit hooks to share with your team:

Terminal window git add .gemini/settings.json

git commit -m "Add project hooks for security and testing"

`.gitignore`

considerations:

# Ignore hook cache and logs

.gemini/memory/session-*.jsonl

Add descriptions to help others understand your hooks:

"matcher" : "write_file|replace" ,

"name" : "secret-scanner" ,

"command" : "$GEMINI_PROJECT_DIR/.gemini/hooks/block-secrets.sh" ,

"description" : "Scans code changes for API keys, passwords, and other secrets before writing"

Add comments in hook scripts:

* This hook reduces the tool space from 100+ tools to ~15 relevant ones

* by extracting keywords from the user's request and filtering tools

* based on semantic similarity.

* Performance: ~500ms average, cached tool embeddings

* Dependencies: @google/generative-ai

Check hook name in `/hooks panel`

:

Verify the hook appears in the list and is enabled.

Verify matcher pattern:

Terminal window echo "write_file|replace" | grep -E "write_.*|replace"

Check disabled list:

"disabled" : [ "my-hook-name" ]

Ensure script is executable:

Terminal window ls -la .gemini/hooks/my-hook.sh

chmod +x .gemini/hooks/my-hook.sh

Verify script path:

Terminal window echo " $GEMINI_PROJECT_DIR /.gemini/hooks/my-hook.sh"

test -f " $GEMINI_PROJECT_DIR /.gemini/hooks/my-hook.sh" && echo "File exists"

Check configured timeout:

Optimize slow operations:

// Before: Sequential operations (slow)

for ( const item of items) {

// After: Parallel operations (fast)

await Promise . all (items. map (( item ) => processItem (item)));

Use caching:

async function getCachedData ( key ) {

const data = await fetchData (key);

Consider splitting into multiple faster hooks:

"command" : "./quick-validation.sh" ,

"command" : "./deep-analysis.sh" ,

Validate JSON before outputting:

output = '{"decision": "allow"}'

if echo " $output " | jq empty 2> /dev/null ; then

echo "Invalid JSON generated" >&2

Ensure proper quoting and escaping:

// Bad: Unescaped string interpolation

const message = `User said: ${ userInput }` ;

console. log ( JSON . stringify ({ message }));

// Good: Automatic escaping

console. log ( JSON . stringify ({ message: `User said: ${ userInput }` }));

Check for binary data or control characters:

function sanitizeForJSON ( str ) {

return str. replace ( / [\x00-\x1F\x7F-\x9F] / g , '' ); // Remove control chars

const cleanContent = sanitizeForJSON (content);

console. log ( JSON . stringify ({ content: cleanContent }));

Verify script returns correct codes:

echo "Validation failed" >&2

Check for unintended errors:

# Don't use 'set -e' if you want to handle errors explicitly

if ! command_that_might_fail ; then

echo "Command failed but continuing" >&2

Use trap for cleanup:

Check if variable is set:

if [ -z " $GEMINI_PROJECT_DIR " ]; then

echo "GEMINI_PROJECT_DIR not set" >&2

if [ -z " $CUSTOM_VAR " ]; then

echo "Warning: CUSTOM_VAR not set, using default" >&2

CUSTOM_VAR = "default-value"

Debug available variables:

# List all environment variables

env > .gemini/hook-env.log

# Check specific variables

echo "GEMINI_PROJECT_DIR: $GEMINI_PROJECT_DIR " >> .gemini/hook-env.log

echo "GEMINI_SESSION_ID: $GEMINI_SESSION_ID " >> .gemini/hook-env.log

echo "GEMINI_API_KEY: ${ GEMINI_API_KEY : + <set> }" >> .gemini/hook-env.log

Use .env files:

# Load .env file if it exists

if [ -f " $GEMINI_PROJECT_DIR /.env" ]; then

source " $GEMINI_PROJECT_DIR /.env"

Understanding where hooks come from and what they can do is critical for secure
usage.

Hook Source Description System Configured by system administrators (e.g., `/etc/gemini-cli/settings.json`

, `/Library/...`

). Assumed to be the safest . User (`~/.gemini/...`

)Configured by you. You are responsible for ensuring they are safe. Extensions You explicitly approve and install these. Security depends on the extension source (integrity). Project (`./.gemini/...`

)Untrusted by default. Safest in trusted internal repos; higher risk in third-party/public repos.

When you open a project with hooks defined in `.gemini/settings.json`

:

Detection : Gemini CLI detects the hooks.
Identification : A unique identity is generated for each hook based on its
`name`

and `command`

.
Warning : If this specific hook identity has not been seen before, a
warning is displayed.
Execution : The hook is executed (unless specific security settings block
it).
Trust : The hook is marked as "trusted" for this project.
[!IMPORTANT] Modification Detection : If the `command`

string of a project
hook is changed (e.g., by a `git pull`

), its identity changes. Gemini CLI will
treat it as a new, untrusted hook and warn you again. This prevents
malicious actors from silently swapping a verified command for a malicious
one.

Risk Description Arbitrary Code Execution Hooks run as your user. They can do anything you can do (delete files, install software). Data Exfiltration A hook could read your input (prompts), output (code), or environment variables (`GEMINI_API_KEY`

) and send them to a remote server. Prompt Injection Malicious content in a file or web page could trick an LLM into running a tool that triggers a hook in an unexpected way.

Verify the source of any project hooks or extensions before enabling them.

For open-source projects, a quick review of the hook scripts is recommended.
For extensions, ensure you trust the author or publisher (e.g., verified
publishers, well-known community members).
Be cautious with obfuscated scripts or compiled binaries from unknown sources.
Hooks inherit the environment of the Gemini CLI process, which may include
sensitive API keys. Gemini CLI attempts to sanitize sensitive variables, but you
should be cautious.

Avoid printing environment variables to stdout/stderr unless necessary.
Use `.env`

files to securely manage sensitive variables, ensuring they are
excluded from version control.
System Administrators: You can enforce environment variable redaction by
default in the system configuration (e.g., `/etc/gemini-cli/settings.json`

):

"environmentVariableRedaction" : {

"blocked" : [ "MY_SECRET_KEY" ],

When writing your own hooks, follow these practices to ensure they are robust
and secure.

Never trust data from hooks without validation. Hook inputs often come from the
LLM or user prompts, which can be manipulated.

# Validate JSON structure

if ! echo " $input " | jq empty 2> /dev/null ; then

echo "Invalid JSON input" >&2

# Validate tool_name explicitly

tool_name = $( echo " $input " | jq -r '.tool_name // empty' )

if [[ " $tool_name " != "write_file" && " $tool_name " != "read_file" ]]; then

echo "Unexpected tool: $tool_name " >&2

Prevent denial-of-service (hanging agents) by enforcing timeouts. Gemini CLI
defaults to 60 seconds, but you should set stricter limits for fast hooks.

"name" : "fast-validator" ,

"command" : "./hooks/validate.sh" ,

"timeout" : 5000 // 5 seconds

Run hooks with minimal required permissions:

if [ " $EUID " -eq 0 ]; then

echo "Hook should not run as root" >&2

# Check file permissions before writing

if [ -w " $file_path " ]; then

echo "Insufficient permissions" >&2

Use `BeforeTool`

hooks to prevent committing sensitive data. This is a powerful
pattern for enhancing security in your workflow.

const SECRET_PATTERNS = [

/api [_-] ? key \s * [:=]\s * ['"] ? [a-zA-Z0-9_-] {20,} ['"] ? / i ,

/password \s * [:=]\s * ['"] ? [ ^ \s'"] {8,} ['"] ? / i ,

/secret \s * [:=]\s * ['"] ? [a-zA-Z0-9_-] {20,} ['"] ? / i ,

/AKIA [0-9A-Z] {16} / , // AWS access key

/ghp_ [a-zA-Z0-9] {36} / , // GitHub personal access token

/sk- [a-zA-Z0-9] {48} / , // OpenAI API key

function containsSecret ( content ) {

return SECRET_PATTERNS . some (( pattern ) => pattern. test (content));

Hook inputs and outputs may contain sensitive information. Gemini CLI respects
the `telemetry.logPrompts`

setting for hook data logging.

Hook telemetry may include:

Hook inputs: User prompts, tool arguments, file contents
Hook outputs: Hook responses, decision reasons, added context
Standard streams: stdout and stderr from hook processes
Execution metadata: Hook name, event type, duration, success/failure
Enabled (default):

Full hook I/O is logged to telemetry. Use this when:

Developing and debugging hooks
Telemetry is redirected to a trusted enterprise system
You understand and accept the privacy implications
Disabled:

Only metadata is logged (event name, duration, success/failure). Hook inputs and
outputs are excluded. Use this when:

Sending telemetry to third-party systems
Working with sensitive data
Privacy regulations require minimizing data collection
Disable PII logging in settings:

Disable via environment variable:

Terminal window export GEMINI_TELEMETRY_LOG_PROMPTS = false

If your hooks process sensitive data:

Minimize logging: Don't write sensitive data to log files
Sanitize outputs: Remove sensitive data before outputting
Use secure storage: Encrypt sensitive data at rest
Limit access: Restrict hook script permissions
Example sanitization:

function sanitizeOutput ( data ) {

const sanitized = { ... data };

// Remove sensitive fields

delete sanitized.password;

// Redact sensitive strings

sanitized.content = sanitized.content. replace (

/api [_-] ? key \s * [:=]\s * ['"] ? [a-zA-Z0-9_-] {20,} ['"] ? / gi ,

console. log ( JSON . stringify ( sanitizeOutput (hookOutput)));