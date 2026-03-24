/**
 * OpenRouter Provider — Cloud LLM via OpenRouter API
 * Used for coding tasks and complex prompts.
 * API key read from process.env.OPENROUTER_API_KEY
 */

import axios from 'axios';

const OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions';
const OPENROUTER_MODEL = process.env.OPENROUTER_MODEL || 'qwen/qwen2.5-coder-7b-instruct';

/**
 * Send messages to OpenRouter and return the response string.
 * @param {Array<{role: string, content: string}>} messages
 * @returns {Promise<string>}
 */
export async function callOpenRouter(messages) {
  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) {
    throw new Error('[OpenRouter] OPENROUTER_API_KEY is not set');
  }

  console.log(`[OpenRouter] Calling model: ${OPENROUTER_MODEL}`);

  const response = await axios.post(OPENROUTER_URL, {
    model: OPENROUTER_MODEL,
    messages,
  }, {
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
      'HTTP-Referer': 'http://localhost:5000',
      'X-Title': 'EVA Assistant',
    },
    timeout: 60_000,
  });

  const content = response.data?.choices?.[0]?.message?.content;
  if (!content) {
    throw new Error('[OpenRouter] Empty response from model');
  }

  return content;
}

export { OPENROUTER_MODEL };
