# Post-Cleanup Smoke Test Plan

Run these 5 tests in order after applying deletions and refactors. Each test validates a critical, non-negotiable feature.

---

## Test 1: Import Chain Integrity
**Validates:** No deleted files break the dependency graph

```bash
cd packages/backend/server

# All Phase 1-3 imports must resolve without error
node -e "import('./src/ai/index.js').then(() => console.log('PASS')).catch(e => { console.error('FAIL:', e.message); process.exit(1); })"
node -e "import('./src/ai/agent/agent.js').then(() => console.log('PASS')).catch(e => { console.error('FAIL:', e.message); process.exit(1); })"
node -e "import('./src/ai/tools/registry.js').then(() => console.log('PASS')).catch(e => { console.error('FAIL:', e.message); process.exit(1); })"
node -e "import('./utils/responseGenerator.js').then(() => console.log('PASS')).catch(e => { console.error('FAIL:', e.message); process.exit(1); })"
```

**Expected:** All 4 print `PASS`. Any `FAIL` means a deleted file was still imported somewhere.

---

## Test 2: Tool Registry Integrity
**Validates:** All 5 tools registered with correct risk levels and schema

```bash
cd packages/backend/server
node -e "
import { getToolRegistry } from './src/ai/tools/registry.js';
const r = getToolRegistry();
const tools = r.listTools();
console.log('Registered tools:', tools.map(t => t.name));
const highRisk = r.getHighRiskTools();
console.log('High-risk tools:', highRisk.map(t => t.name));

// Verify all 5 core tools are present
const expected = ['read_file', 'write_file', 'run_command', 'search_files', 'fetch_url'];
const missing = expected.filter(n => !tools.find(t => t.name === n));
if (missing.length > 0) { console.error('FAIL: Missing tools:', missing); process.exit(1); }

// Verify risk levels
const shell = r.findTool('run_command');
if (shell?.risk_level !== 'high') { console.error('FAIL: shell should be high-risk'); process.exit(1); }

console.log('PASS: All tools registered correctly');
"
```

**Expected:** `PASS: All tools registered correctly` with all 5 tool names listed. High-risk should include `run_command` and `write_file`.

---

## Test 3: Agent Pipeline (No LLM)
**Validates:** Intent detection → subagent routing → planner → executor chain works end-to-end

```bash
cd packages/backend/server
node -e "
import { detectIntent } from './src/ai/intent.js';
import { findSubagent, listSubagents } from './src/ai/agents/subagents.js';
import { getToolRegistry } from './src/ai/tools/registry.js';

// Test intent detection
const chatIntent = detectIntent('Hello, how are you?', { structured: true });
if (chatIntent.intent !== 'CHAT') { console.error('FAIL: Expected CHAT, got', chatIntent.intent); process.exit(1); }

const taskIntent = detectIntent('Create a new React project with TypeScript', { structured: true });
if (taskIntent.intent !== 'TASK') { console.error('FAIL: Expected TASK, got', taskIntent.intent); process.exit(1); }

const searchIntent = detectIntent('What is the capital of France?', { structured: true });
if (searchIntent.intent !== 'SEARCH') { console.error('FAIL: Expected SEARCH, got', searchIntent.intent); process.exit(1); }

// Test subagent availability
const subs = listSubagents();
if (subs.length < 4) { console.error('FAIL: Expected 4 subagents, got', subs.length); process.exit(1); }

// Test tool registry
const registry = getToolRegistry();
if (registry.listTools().length < 5) { console.error('FAIL: Expected 5+ tools'); process.exit(1); }

console.log('PASS: Pipeline components initialized');
"
```

**Expected:** `PASS: Pipeline components initialized` with correct intent classifications.

---

## Test 4: TypeScript Build
**Validates:** Frontend compiles without errors after all backend changes

```bash
cd packages/frontend
npx tsc --noEmit
```

**Expected:** Exit code 0, no output. Any type error means a frontend component references a deleted/changed backend contract.

---

## Test 5: Server Startup (Dry Run)
**Validates:** Both servers can start without import errors

```bash
# Node.js server (will hang on setInterval — that's expected, kill with Ctrl+C)
cd packages/backend/server
timeout 5 node server.js 2>&1 || true

# Verify Python app imports cleanly
python -c "
import sys
sys.path.insert(0, '.')
from app import app
print('Flask app imported successfully')
" 2>&1
```

**Expected:** Node.js server starts (timeout kills it after 5s — that's fine). Python prints `Flask app imported successfully`. Any import error means a deleted Python file was still referenced.

---

## Failure Recovery

If any test fails:
1. `git diff --name-only` to see what was changed
2. `git checkout -- <file>` to restore a specific file
3. Re-run the failing test to confirm the fix
