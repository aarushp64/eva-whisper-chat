/**
 * Router — Model selection with runtime config override
 *
 * Active providers: Groq (cloud, fast) → Ollama (local, private)
 *
 * Routing rules (when no runtime config):
 *   - Coding/long prompts → Groq
 *   - Everything else → Ollama (local, free)
 *
 * Runtime config: if `{ provider, model, apiKey }` is passed, use that
 * provider directly with automatic fallback to Ollama.
 *
 * Fallback chain: selected → ollama → error message
 */

import { callOllama, OLLAMA_MODEL } from './providers/ollama.js';
import { callGroq, GROQ_MODEL } from './providers/groq.js';
import { getMemory } from './memory.js';

// Keywords that indicate a coding-related or complex prompt → use Groq
const COMPLEX_KEYWORDS = [
  'code', 'bug', 'function', 'error', 'debug', 'syntax', 'compile',
  'api', 'script', 'variable', 'class', 'import', 'module', 'package',
  'npm', 'git', 'deploy', 'server', 'database', 'query', 'regex',
  'algorithm', 'loop', 'array', 'object', 'promise', 'async', 'await',
  'architecture', 'design', 'system', 'refactor', 'pattern', 'structure',
  'scale', 'migration', 'infrastructure', 'microservice', 'monolith',
];

/**
 * Analyze the last user message and decide which provider to use.
 * @param {string} content — the user's message text
 * @returns {'ollama' | 'groq'}
 */
function selectProvider(content) {
  const lower = content.toLowerCase();
  if (COMPLEX_KEYWORDS.some(kw => lower.includes(kw)) || content.length > 500) {
    return 'groq';
  }
  return 'ollama';
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

  // Build fallback chain: selected first, then the other, then ultimate ollama fallback
  const fallbackChain = runtimeProvider
    ? [runtimeProvider, selected === runtimeProvider ? 'ollama' : 'ollama']
    : [selected, selected === 'ollama' ? 'groq' : 'ollama'];
  // Deduplicate
  const uniqueChain = [...new Set(fallbackChain)];

  // Provider call configurations
  const providerConfigs = {
    ollama: {
      call: callOllama,
      model: OLLAMA_MODEL,
      label: 'Ollama (local)',
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

  for (const providerName of uniqueChain) {
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

  console.error('[Router] All providers failed. Returning error message.');
  return 'I apologize, but I\'m having trouble connecting to my AI models right now. Please try again shortly.';
}

export { selectProvider };
