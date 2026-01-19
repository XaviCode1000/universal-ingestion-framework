---
url: https://geminicli.com/docs/hooks/writing-hooks
title: Writing hooks for Gemini CLI
author: null
date: null
sitename: Gemini CLI
ingestion_engine: UIF v2.0 (Elite Optimized)
---

This guide will walk you through creating hooks for Gemini CLI, from a simple
logging hook to a comprehensive workflow assistant that demonstrates all hook
events working together.

Before you start, make sure you have:

Gemini CLI installed and configured
Basic understanding of shell scripting or JavaScript/Node.js
Familiarity with JSON for hook input/output
Let's create a simple hook that logs all tool executions to understand the
basics.

Create a directory for hooks and a simple logging script:

cat > .gemini/hooks/log-tools.sh << 'EOF'

# Read hook input from stdin

tool_name=$(echo "$input" | jq -r '.tool_name')

echo "[$(date)] Tool executed: $tool_name" >> .gemini/tool-log.txt

# Return success (exit 0) - output goes to user in transcript mode

echo "Logged: $tool_name"

chmod +x .gemini/hooks/log-tools.sh

Add the hook configuration to `.gemini/settings.json`

:

"command" : "$GEMINI_PROJECT_DIR/.gemini/hooks/log-tools.sh" ,

"description" : "Log all tool executions"

Run Gemini CLI and execute any command that uses tools:

> Read the README.md file

[Agent uses read_file tool]

Check `.gemini/tool-log.txt`

to see the logged tool executions.

Prevent committing files containing API keys or passwords.

`.gemini/hooks/block-secrets.sh`

:

# Extract content being written

content = $( echo " $input " | jq -r '.tool_input.content // .tool_input.new_string // ""' )

if echo " $content " | grep -qE 'api[_-]?key|password|secret' ; then

echo '{"decision":"deny","reason":"Potential secret detected"}' >&2

`.gemini/settings.json`

:

"matcher" : "write_file|replace" ,

"name" : "secret-scanner" ,

"command" : "$GEMINI_PROJECT_DIR/.gemini/hooks/block-secrets.sh" ,

"description" : "Prevent committing secrets"

Automatically run tests when code files are modified.

`.gemini/hooks/auto-test.sh`

:

file_path = $( echo " $input " | jq -r '.tool_input.file_path' )

if [[ ! " $file_path " =~ \. ts$ ]]; then

# Find corresponding test file

test_file = "${ file_path % . ts }.test.ts"

if [ ! -f " $test_file " ]; then

echo "⚠️ No test file found"

if npx vitest run " $test_file " --silent 2>&1 | head -20 ; then

`.gemini/settings.json`

:

"matcher" : "write_file|replace" ,

"command" : "$GEMINI_PROJECT_DIR/.gemini/hooks/auto-test.sh" ,

"description" : "Run tests after code changes"

Add relevant project context before each agent interaction.

`.gemini/hooks/inject-context.sh`

:

# Get recent git commits for context

context = $( git log -5 --oneline 2> /dev/null || echo "No git history" )

"hookEventName": "BeforeAgent",

"additionalContext": "Recent commits:\n $context "

`.gemini/settings.json`

:

"command" : "$GEMINI_PROJECT_DIR/.gemini/hooks/inject-context.sh" ,

"description" : "Inject git commit history"

Use `BeforeToolSelection`

to intelligently reduce the tool space based on the
current task. Instead of sending all 100+ tools to the model, filter to the most
relevant ~15 tools using semantic search or keyword matching.

This improves:

Model accuracy: Fewer similar tools reduce confusion
Response speed: Smaller tool space is faster to process
Cost efficiency: Less tokens used per request
Use `SessionStart`

and `SessionEnd`

hooks to maintain persistent knowledge
across sessions:

SessionStart: Load relevant memories from previous sessions
AfterModel: Record important interactions during the session
SessionEnd: Extract learnings and store for future use
This enables the assistant to learn project conventions, remember important
decisions, and share knowledge across team members.

Multiple hooks for the same event run in the order declared. Each hook can build
upon previous hooks' outputs:

"command" : "./hooks/load-memories.sh"

"name" : "analyze-sentiment" ,

"command" : "./hooks/analyze-sentiment.sh"

This comprehensive example demonstrates all hook events working together with
two advanced features:

RAG-based tool selection: Reduces 100+ tools to ~15 relevant ones per task
Cross-session memory: Learns and persists project knowledge
SessionStart → Initialize memory & index tools

BeforeAgent → Inject relevant memories

BeforeModel → Add system instructions

BeforeToolSelection → Filter tools via RAG

BeforeTool → Validate security

AfterTool → Run auto-tests

AfterModel → Record interaction

SessionEnd → Extract and store memories

Prerequisites:

Node.js 18+
Gemini CLI installed
Setup:

Terminal window mkdir -p .gemini/hooks .gemini/memory

npm install --save-dev chromadb @google/generative-ai

# Copy hook scripts (shown below)

chmod +x .gemini/hooks/ * .js

`.gemini/settings.json`

:

"name" : "init-assistant" ,

"command" : "node $GEMINI_PROJECT_DIR/.gemini/hooks/init.js" ,

"description" : "Initialize Smart Workflow Assistant"

"name" : "inject-memories" ,

"command" : "node $GEMINI_PROJECT_DIR/.gemini/hooks/inject-memories.js" ,

"description" : "Inject relevant project memories"

"command" : "node $GEMINI_PROJECT_DIR/.gemini/hooks/rag-filter.js" ,

"description" : "Filter tools using RAG"

"matcher" : "write_file|replace" ,

"name" : "security-check" ,

"command" : "node $GEMINI_PROJECT_DIR/.gemini/hooks/security.js" ,

"description" : "Prevent committing secrets"

"matcher" : "write_file|replace" ,

"command" : "node $GEMINI_PROJECT_DIR/.gemini/hooks/auto-test.js" ,

"description" : "Run tests after code changes"

"name" : "record-interaction" ,

"command" : "node $GEMINI_PROJECT_DIR/.gemini/hooks/record.js" ,

"description" : "Record interaction for learning"

"matcher" : "exit|logout" ,

"name" : "consolidate-memories" ,

"command" : "node $GEMINI_PROJECT_DIR/.gemini/hooks/consolidate.js" ,

"description" : "Extract and store session learnings"

`.gemini/hooks/init.js`

:

const { ChromaClient } = require ( 'chromadb' );

const path = require ( 'path' );

const fs = require ( 'fs' );

const projectDir = process.env. GEMINI_PROJECT_DIR ;

const chromaPath = path. join (projectDir, '.gemini' , 'chroma' );

// Ensure chroma directory exists

fs. mkdirSync (chromaPath, { recursive: true });

const client = new ChromaClient ({ path: chromaPath });

// Initialize memory collection

await client. getOrCreateCollection ({

name: 'project_memories' ,

metadata: { 'hnsw:space' : 'cosine' },

// Count existing memories

const collection = await client. getCollection ({ name: 'project_memories' });

const memoryCount = await collection. count ();

hookEventName: 'SessionStart' ,

additionalContext: `Smart Workflow Assistant initialized with ${ memoryCount } project memories.` ,

systemMessage: `🧠 ${ memoryCount } memories loaded` ,

return new Promise (( resolve ) => {

process.stdin. on ( 'data' , ( chunk ) => chunks. push (chunk));

process.stdin. on ( 'end' , () => resolve (Buffer. concat (chunks). toString ()));

readStdin (). then (main). catch (console.error);

`.gemini/hooks/inject-memories.js`

:

const { GoogleGenerativeAI } = require ( '@google/generative-ai' );

const { ChromaClient } = require ( 'chromadb' );

const path = require ( 'path' );

const input = JSON . parse ( await readStdin ());

const { prompt } = input;

console. log ( JSON . stringify ({}));

const genai = new GoogleGenerativeAI (process.env. GEMINI_API_KEY );

const model = genai. getGenerativeModel ({ model: 'text-embedding-004' });

const result = await model. embedContent (prompt);

const projectDir = process.env. GEMINI_PROJECT_DIR ;

const client = new ChromaClient ({

path: path. join (projectDir, '.gemini' , 'chroma' ),

const collection = await client. getCollection ({ name: 'project_memories' });

const results = await collection. query ({

queryEmbeddings: [result.embedding.values],

if (results.documents[ 0 ]?. length > 0 ) {

const memories = results.documents[ 0 ]

const meta = results.metadatas[ 0 ][i];

return `- [${ meta . category }] ${ meta . summary }` ;

hookEventName: 'BeforeAgent' ,

additionalContext: ` \n ## Relevant Project Context \n\n ${ memories } \n ` ,

systemMessage: `💭 ${ results . documents [ 0 ]. length } memories recalled` ,

console. log ( JSON . stringify ({}));

console. log ( JSON . stringify ({}));

return new Promise (( resolve ) => {

process.stdin. on ( 'data' , ( chunk ) => chunks. push (chunk));

process.stdin. on ( 'end' , () => resolve (Buffer. concat (chunks). toString ()));

readStdin (). then (main). catch (console.error);

`.gemini/hooks/rag-filter.js`

:

const { GoogleGenerativeAI } = require ( '@google/generative-ai' );

const input = JSON . parse ( await readStdin ());

const { llm_request } = input;

llm_request.toolConfig?.functionCallingConfig?.allowedFunctionNames || [];

// Skip if already filtered

if (candidateTools. length <= 20 ) {

console. log ( JSON . stringify ({}));

// Extract recent user messages

const recentMessages = llm_request.messages

. filter (( m ) => m.role === 'user' )

// Use fast model to extract task keywords

const genai = new GoogleGenerativeAI (process.env. GEMINI_API_KEY );

const model = genai. getGenerativeModel ({ model: 'gemini-2.0-flash-exp' });

const result = await model. generateContent (

`Extract 3-5 keywords describing needed tool capabilities from this request: \n\n ${ recentMessages } \n\n Keywords (comma-separated):` ,

const keywords = result.response

// Simple keyword-based filtering + core tools

const coreTools = [ 'read_file' , 'write_file' , 'replace' , 'run_shell_command' ];

const filtered = candidateTools. filter (( tool ) => {

if (coreTools. includes (tool)) return true ;

const toolLower = tool. toLowerCase ();

( kw ) => toolLower. includes (kw) || kw. includes (toolLower),

hookEventName: 'BeforeToolSelection' ,

allowedFunctionNames: filtered. slice ( 0 , 20 ),

systemMessage: `🎯 Filtered ${ candidateTools . length } → ${ Math . min ( filtered . length , 20 ) } tools` ,

return new Promise (( resolve ) => {

process.stdin. on ( 'data' , ( chunk ) => chunks. push (chunk));

process.stdin. on ( 'end' , () => resolve (Buffer. concat (chunks). toString ()));

readStdin (). then (main). catch (console.error);

`.gemini/hooks/security.js`

:

const SECRET_PATTERNS = [

/api [_-] ? key \s * [:=]\s * ['"] ? [a-zA-Z0-9_-] {20,} ['"] ? / i ,

/password \s * [:=]\s * ['"] ? [ ^ \s'"] {8,} ['"] ? / i ,

/secret \s * [:=]\s * ['"] ? [a-zA-Z0-9_-] {20,} ['"] ? / i ,

/AKIA [0-9A-Z] {16} / , // AWS

/ghp_ [a-zA-Z0-9] {36} / , // GitHub

const input = JSON . parse ( await readStdin ());

const { tool_input } = input;

const content = tool_input.content || tool_input.new_string || '' ;

for ( const pattern of SECRET_PATTERNS ) {

if (pattern. test (content)) {

'Potential secret detected in code. Please remove sensitive data.' ,

systemMessage: '🚨 Secret scanner blocked operation' ,

console. log ( JSON . stringify ({ decision: 'allow' }));

return new Promise (( resolve ) => {

process.stdin. on ( 'data' , ( chunk ) => chunks. push (chunk));

process.stdin. on ( 'end' , () => resolve (Buffer. concat (chunks). toString ()));

readStdin (). then (main). catch (console.error);

`.gemini/hooks/auto-test.js`

:

const { execSync } = require ( 'child_process' );

const fs = require ( 'fs' );

const path = require ( 'path' );

const input = JSON . parse ( await readStdin ());

const { tool_input } = input;

const filePath = tool_input.file_path;

if ( ! filePath?. match ( / \. (ts | js | tsx | jsx) $ / )) {

console. log ( JSON . stringify ({}));

const ext = path. extname (filePath);

const base = filePath. slice ( 0 , - ext. length );

const testFile = `${ base }.test${ ext }` ;

if ( ! fs. existsSync (testFile)) {

systemMessage: `⚠️ No test file: ${ path . basename ( testFile ) }` ,

execSync ( `npx vitest run ${ testFile } --silent` , {

systemMessage: `✅ Tests passed: ${ path . basename ( filePath ) }` ,

systemMessage: `❌ Tests failed: ${ path . basename ( filePath ) }` ,

return new Promise (( resolve ) => {

process.stdin. on ( 'data' , ( chunk ) => chunks. push (chunk));

process.stdin. on ( 'end' , () => resolve (Buffer. concat (chunks). toString ()));

readStdin (). then (main). catch (console.error);

`.gemini/hooks/record.js`

:

const fs = require ( 'fs' );

const path = require ( 'path' );

const input = JSON . parse ( await readStdin ());

const { llm_request , llm_response } = input;

const projectDir = process.env. GEMINI_PROJECT_DIR ;

const sessionId = process.env. GEMINI_SESSION_ID ;

const tempFile = path. join (

`session-${ sessionId }.jsonl` ,

fs. mkdirSync (path. dirname (tempFile), { recursive: true });

// Extract user message and model response

const userMsg = llm_request.messages

?. filter (( m ) => m.role === 'user' )

const modelMsg = llm_response.candidates?.[ 0 ]?.content?.parts

if (userMsg && modelMsg) {

timestamp: new Date (). toISOString (),

user: process.env. USER || 'unknown' ,

request: userMsg. slice ( 0 , 500 ), // Truncate for storage

response: modelMsg. slice ( 0 , 500 ),

fs. appendFileSync (tempFile, JSON . stringify (interaction) + ' \n ' );

console. log ( JSON . stringify ({}));

return new Promise (( resolve ) => {

process.stdin. on ( 'data' , ( chunk ) => chunks. push (chunk));

process.stdin. on ( 'end' , () => resolve (Buffer. concat (chunks). toString ()));

readStdin (). then (main). catch (console.error);

`.gemini/hooks/consolidate.js`

:

const fs = require ( 'fs' );

const path = require ( 'path' );

const { GoogleGenerativeAI } = require ( '@google/generative-ai' );

const { ChromaClient } = require ( 'chromadb' );

const input = JSON . parse ( await readStdin ());

const projectDir = process.env. GEMINI_PROJECT_DIR ;

const sessionId = process.env. GEMINI_SESSION_ID ;

const tempFile = path. join (

`session-${ sessionId }.jsonl` ,

if ( ! fs. existsSync (tempFile)) {

console. log ( JSON . stringify ({}));

. readFileSync (tempFile, 'utf8' )

. map (( line ) => JSON . parse (line));

if (interactions. length === 0 ) {

console. log ( JSON . stringify ({}));

// Extract memories using LLM

const genai = new GoogleGenerativeAI (process.env. GEMINI_API_KEY );

const model = genai. getGenerativeModel ({ model: 'gemini-2.0-flash-exp' });

const prompt = `Extract important project learnings from this session.

Focus on: decisions, conventions, gotchas, patterns.

Return JSON array with: category, summary, keywords

${ JSON . stringify ( interactions , null , 2 ) }

const result = await model. generateContent (prompt);

const text = result.response. text (). replace ( /```json \n ?| \n ? ```/ g , '' );

const memories = JSON . parse (text);

const client = new ChromaClient ({

path: path. join (projectDir, '.gemini' , 'chroma' ),

const collection = await client. getCollection ({ name: 'project_memories' });

const embedModel = genai. getGenerativeModel ({

model: 'text-embedding-004' ,

for ( const memory of memories) {

const memoryText = `${ memory . category }: ${ memory . summary }` ;

const embedding = await embedModel. embedContent (memoryText);

const id = `${ Date . now () }-${ Math . random (). toString ( 36 ). slice ( 2 ) }` ;

embeddings: [embedding.embedding.values],

category: memory.category || 'general' ,

keywords: (memory.keywords || []). join ( ',' ),

timestamp: new Date (). toISOString (),

systemMessage: `🧠 ${ memories . length } new learnings saved for future sessions` ,

console. error ( 'Error consolidating memories:' , error);

console. log ( JSON . stringify ({}));

return new Promise (( resolve ) => {

process.stdin. on ( 'data' , ( chunk ) => chunks. push (chunk));

process.stdin. on ( 'end' , () => resolve (Buffer. concat (chunks). toString ()));

readStdin (). then (main). catch (console.error);

> Fix the authentication bug in login.ts

- [convention] Use middleware pattern for auth

- [gotcha] Remember to update token types

🎯 Filtered 127 → 15 tools

[Agent reads login.ts and proposes fix]

> Add error logging to API endpoints

- [convention] Use middleware pattern for auth

- [pattern] Centralized error handling in middleware

- [decision] Log errors to CloudWatch

🎯 Filtered 127 → 18 tools

[Agent implements error logging]

🧠 2 new learnings saved for future sessions

RAG-based tool selection:

Traditional: Send all 100+ tools causing confusion and context overflow
This example: Extract intent, filter to ~15 relevant tools
Benefits: Faster responses, better selection, lower costs
Cross-session memory:

Traditional: Each session starts fresh
This example: Learns conventions, decisions, gotchas, patterns
Benefits: Shared knowledge across team members, persistent learnings
All hook events integrated:

Demonstrates every hook event with practical use cases in a cohesive workflow.

Uses `gemini-2.0-flash-exp`

for intent extraction (fast, cheap)
Uses `text-embedding-004`

for RAG (inexpensive)
Caches tool descriptions (one-time cost)
Minimal overhead per request (<500ms typically)
Adjust memory relevance:

// In inject-memories.js, change nResults

const results = await collection. query ({

queryEmbeddings: [result.embedding.values],

nResults: 5 , // More memories

Modify tool filter count:

// In rag-filter.js, adjust the limit

allowedFunctionNames : filtered. slice ( 0 , 30 ), // More tools

Add custom security patterns:

// In security.js, add patterns

const SECRET_PATTERNS = [

While project-level hooks are great for specific repositories, you might want to
share your hooks across multiple projects or with other users. You can do this
by packaging your hooks as a Gemini CLI extension .

Packaging as an extension provides:

Easy distribution: Share hooks via a git repository or GitHub release.
Centralized management: Install, update, and disable hooks using
`gemini extensions`

commands.
Version control: Manage hook versions separately from your project code.
Variable substitution: Use `${extensionPath}`

and `${process.execPath}`

for portable, cross-platform scripts.
To package hooks as an extension, follow the
extensions hook documentation .