/**
 * Router — Intelligent model selection based on prompt analysis
 *
 * Routing rules:
 *   - Coding keywords → OpenRouter (Qwen Coder)
 *   - Long prompts (>500 chars) or architecture keywords → OpenRouter
 *   - Everything else → Local Ollama (free)
 *
 * Fallback chain: selected → Ollama → OpenRouter → Anthropic → error message
 */

import { callOllama, OLLAMA_MODEL } from './providers/ollama.js';
import { callOpenRouter, OPENROUTER_MODEL } from './providers/openrouter.js';
import { callAnthropic, ANTHROPIC_MODEL } from './providers/anthropic.js';
import { getMemory } from './memory.js';

// Keywords that indicate a coding-related prompt
const CODING_KEYWORDS = [
  'code', 'bug', 'function', 'error', 'debug', 'syntax', 'compile',
  'api', 'script', 'variable', 'class', 'import', 'module', 'package',
  'npm', 'git', 'deploy', 'server', 'database', 'query', 'regex',
  'algorithm', 'loop', 'array', 'object', 'promise', 'async', 'await',
];

// Keywords that indicate architecture / design prompts
const ARCHITECTURE_KEYWORDS = [
  'architecture', 'design', 'system', 'refactor', 'pattern', 'structure',
  'scale', 'migration', 'infrastructure', 'microservice', 'monolith',
];

/**
 * Analyze the last user message and decide which provider to use.
 * @param {string} content — the user's message text
 * @returns {'ollama' | 'openrouter'}
 */
function selectProvider(content) {
  const lower = content.toLowerCase();

  // Rule 1: coding keywords → OpenRouter
  if (CODING_KEYWORDS.some(kw => lower.includes(kw))) {
    return 'openrouter';
  }

  // Rule 2: long prompt or architecture keywords → OpenRouter
  if (content.length > 500 || ARCHITECTURE_KEYWORDS.some(kw => lower.includes(kw))) {
    return 'openrouter';
  }

  // Default: local Ollama
  return 'ollama';
}

/**
 * Route a prompt to the best available model, with automatic fallback.
 * Prepends conversation memory to the messages array.
 *
 * @param {Array<{role: string, content: string}>} messages
 * @returns {Promise<string>} — the model's response text
 */
export async function routePrompt(messages) {
  // Prepend conversation memory for context continuity
  const memory = getMemory();
  const fullMessages = [...memory, ...messages];

  // Determine the user's latest message for routing analysis
  const lastUserMsg = [...messages].reverse().find(m => m.role === 'user');
  const content = lastUserMsg?.content || '';

  const selected = selectProvider(content);

  // Map provider names to call functions and display names
  const providers = {
    ollama:     { call: callOllama,     model: OLLAMA_MODEL },
    openrouter: { call: callOpenRouter, model: OPENROUTER_MODEL },
    anthropic:  { call: callAnthropic,  model: ANTHROPIC_MODEL },
  };

  // Build ordered fallback chain starting from the selected provider
  const fallbackOrder = selected === 'ollama'
    ? ['ollama', 'openrouter', 'anthropic']
    : ['openrouter', 'ollama', 'anthropic'];

  for (const providerName of fallbackOrder) {
    try {
      console.log(`[Router] Using model: ${providers[providerName].model} (${providerName})`);
      const response = await providers[providerName].call(fullMessages);
      return response;
    } catch (err) {
      console.warn(`[Router] ${providerName} failed: ${err.message}`);
      console.log(`[Router] Falling back to next provider...`);
    }
  }

  // All providers failed
  console.error('[Router] All providers failed. Returning error message.');
  return 'I apologize, but I\'m having trouble connecting to my AI models right now. Please try again shortly.';
}

export { selectProvider };
