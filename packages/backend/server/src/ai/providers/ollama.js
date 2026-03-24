/**
 * Ollama Provider — Local LLM inference via Ollama API
 * Default/free provider. Model configurable via OLLAMA_MODEL env var.
 */

import axios from 'axios';

const OLLAMA_URL = process.env.OLLAMA_URL || 'http://localhost:11434';
const OLLAMA_MODEL = process.env.OLLAMA_MODEL || 'qwen3:8b';

/**
 * Send messages to local Ollama instance and return the response string.
 * @param {Array<{role: string, content: string}>} messages
 * @returns {Promise<string>}
 */
export async function callOllama(messages) {
  console.log(`[Ollama] Calling model: ${OLLAMA_MODEL}`);

  const response = await axios.post(`${OLLAMA_URL}/api/chat`, {
    model: OLLAMA_MODEL,
    messages,
    stream: false,
  }, {
    timeout: 120_000, // 2 minute timeout for local inference
  });

  const content = response.data?.message?.content;
  if (!content) {
    throw new Error('[Ollama] Empty response from model');
  }

  return content;
}

export { OLLAMA_MODEL };
