/**
 * Router — Intelligent model selection with runtime config override
 *
 * Routing rules (when no runtime config is provided):
 *   - Coding keywords → OpenRouter (Qwen Coder)
 *   - Long prompts (>500 chars) or architecture keywords → OpenRouter
 *   - Everything else → Local Ollama (free)
 *
 * Runtime config: if `{ provider, model, apiKey }` is passed, use that
 * provider directly with automatic fallback chain.
 *
 * Fallback chain: selected → ollama → openrouter → anthropic → error message
 */

import { callOllama, OLLAMA_MODEL } from './providers/ollama.js';
import { callOpenRouter, OPENROUTER_MODEL } from './providers/openrouter.js';
import { callAnthropic, ANTHROPIC_MODEL } from './providers/anthropic.js';
import { callGroq, GROQ_MODEL } from './providers/groq.js';
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

// Default fallback: ollama model used when all else fails
const DEFAULT_FALLBACK_MODEL = process.env.OLLAMA_FALLBACK_MODEL || 'qwen3.5:9b';

/**
 * Analyze the last user message and decide which provider to use.
 * @param {string} content — the user's message text
 * @returns {'ollama' | 'openrouter' | 'groq'}
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
 * Build the ordered fallback chain starting from a selected provider.
 *
 * @param {string} selected — the initially selected provider name
 * @param {string} [runtimeProvider] — runtime-configured provider (takes priority)
 * @returns {string[]}
 */
function buildFallbackChain(selected, runtimeProvider) {
  // If a runtime provider was explicitly selected, start from it
  const allProviders = ['groq', 'openrouter', 'ollama', 'anthropic'];
  const baseChain = selected === 'ollama'
    ? ['ollama', 'openrouter', 'groq', 'anthropic']
    : [selected, 'ollama', 'openrouter', 'groq', 'anthropic'];

  if (runtimeProvider && allProviders.includes(runtimeProvider)) {
    // Put the runtime provider first, then the rest preserving order
    const others = baseChain.filter(p => p !== runtimeProvider);
    return [runtimeProvider, ...others];
  }

  return baseChain;
}

/**
 * Route a prompt to the best available model, with automatic fallback.
 * Prepends conversation memory to the messages array.
 *
 * @param {Array<{role: string, content: string}>} messages
 * @param {{provider?: string, model?: string, apiKey?: string}} [runtimeConfig]
 * @returns {Promise<string>} — the model's response text
 */
export async function routePrompt(messages, runtimeConfig) {
  const memory = getMemory();
  const fullMessages = [...memory, ...messages];

  const lastUserMsg = [...messages].reverse().find(m => m.role === 'user');
  const content = lastUserMsg?.content || '';

  const runtimeProvider = runtimeConfig?.provider;
  const selected = runtimeProvider || selectProvider(content);

  const fallbackChain = buildFallbackChain(selected, runtimeProvider);

  // Provider call configurations
  const providerConfigs = {
    ollama: {
      call: callOllama,
      model: runtimeConfig?.provider === 'ollama' ? runtimeConfig.model : OLLAMA_MODEL,
      label: 'Ollama (local)',
    },
    openrouter: {
      call: callOpenRouter,
      model: OPENROUTER_MODEL,
      label: 'OpenRouter (cloud)',
    },
    anthropic: {
      call: callAnthropic,
      model: ANTHROPIC_MODEL,
      label: 'Anthropic (premium)',
    },
    groq: {
      call: (msgs) => callGroq(msgs, {
        apiKey: runtimeConfig?.apiKey,
        model: runtimeConfig?.provider === 'groq' ? runtimeConfig.model : GROQ_MODEL,
      }),
      model: runtimeConfig?.provider === 'groq' ? runtimeConfig.model : GROQ_MODEL,
      label: 'Groq (cloud)',
    },
  };

  for (const providerName of fallbackChain) {
    const config = providerConfigs[providerName];
    if (!config) continue;

    try {
      console.log(`[Router] Using: ${config.label} — ${config.model}`);
      const response = await config.call(fullMessages);
      return response;
    } catch (err) {
      const isApiKeyError = err.message?.includes('API_KEY') || err.message?.includes('not set');
      if (isApiKeyError) {
        console.warn(`[Router] ${providerName} skipped: missing API key`);
      } else {
        console.warn(`[Router] ${providerName} failed: ${err.message}`);
      }
      console.log(`[Router] Falling back to next provider...`);
    }
  }

  // Ultimate fallback: try the default ollama fallback model
  try {
    console.log(`[Router] Ultimate fallback: Ollama ${DEFAULT_FALLBACK_MODEL}`);
    const { callOllama: fallbackCall } = await import('./providers/ollama.js');
    // Temporarily override model via env for this call
    const origModel = process.env.OLLAMA_MODEL;
    process.env.OLLAMA_MODEL = DEFAULT_FALLBACK_MODEL;
    const response = await fallbackCall(fullMessages);
    process.env.OLLAMA_MODEL = origModel;
    return response;
  } catch {
    console.error('[Router] All providers failed. Returning error message.');
    return 'I apologize, but I\'m having trouble connecting to my AI models right now. Please try again shortly.';
  }
}

export { selectProvider };
