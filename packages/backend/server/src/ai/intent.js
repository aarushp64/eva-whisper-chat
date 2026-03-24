/**
 * Intent Detection — classify user input into actionable intent categories
 *
 * Uses keyword-based heuristics to determine how the system should handle
 * the request: simple chat, multi-step task, direct action, or search.
 */

// Keywords for each intent category
const TASK_KEYWORDS = [
  'create', 'build', 'make', 'generate', 'implement', 'set up', 'setup',
  'configure', 'install', 'deploy', 'migrate', 'convert', 'transform',
  'refactor', 'optimize', 'update', 'upgrade', 'add', 'remove', 'delete',
  'fix', 'solve', 'automate', 'write a script', 'write code', 'develop',
  'plan', 'design', 'architect', 'restructure', 'organize',
];

const ACTION_KEYWORDS = [
  'run', 'execute', 'open', 'read file', 'write file', 'show file',
  'list files', 'cat', 'ls', 'dir', 'pwd', 'cd', 'fetch', 'download',
  'curl', 'ping', 'check status', 'restart', 'stop', 'start',
  'kill', 'npm', 'node', 'git', 'pip',
];

const SEARCH_KEYWORDS = [
  'search', 'find', 'look for', 'where is', 'locate', 'grep', 'lookup',
  'what is', 'who is', 'how to', 'explain', 'tell me about', 'define',
];

/**
 * Detect the user's intent from their input text.
 *
 * @param {string} input — the user's message
 * @returns {'CHAT' | 'TASK' | 'ACTION' | 'SEARCH'}
 */
export function detectIntent(input) {
  const lower = input.toLowerCase();

  // Check ACTION first — most specific (direct commands)
  if (ACTION_KEYWORDS.some(kw => lower.includes(kw))) {
    console.log('[Intent] Detected: ACTION');
    return 'ACTION';
  }

  // Check TASK — multi-step work
  if (TASK_KEYWORDS.some(kw => lower.includes(kw))) {
    console.log('[Intent] Detected: TASK');
    return 'TASK';
  }

  // Check SEARCH — information lookup
  if (SEARCH_KEYWORDS.some(kw => lower.includes(kw))) {
    console.log('[Intent] Detected: SEARCH');
    return 'SEARCH';
  }

  // Default: conversational chat
  console.log('[Intent] Detected: CHAT');
  return 'CHAT';
}
