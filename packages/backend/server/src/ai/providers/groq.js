/**
 * Groq Provider — Cloud LLM via Groq SDK with streaming
 *
 * API key is passed per-request from runtime config.
 * Never persisted to disk, localStorage, or git.
 */

import { Groq } from 'groq-sdk';

const DEFAULT_MODEL = process.env.GROQ_MODEL || 'qwen/qwen3-32b';
const DEFAULT_TEMPERATURE = 0.6;
const DEFAULT_MAX_TOKENS = 4096;

/**
 * Send messages to Groq and return the full response string.
 * Non-streaming path for backward compatibility with routePrompt().
 *
 * @param {Array<{role: string, content: string}>} messages
 * @param {{apiKey?: string, model?: string}} options
 * @returns {Promise<string>}
 */
export async function callGroq(messages, options = {}) {
  const apiKey = options.apiKey || process.env.GROQ_API_KEY;
  if (!apiKey) {
    throw new Error('[Groq] GROQ_API_KEY is not set');
  }

  const model = options.model || DEFAULT_MODEL;
  console.log(`[Groq] Calling model: ${model}`);

  const client = new Groq({ apiKey });

  const completion = await client.chat.completions.create({
    model,
    messages,
    temperature: DEFAULT_TEMPERATURE,
    max_completion_tokens: DEFAULT_MAX_TOKENS,
    top_p: 0.95,
    stream: false,
  });

  const content = completion.choices?.[0]?.message?.content;
  if (!content) {
    throw new Error('[Groq] Empty response from model');
  }

  return content;
}

/**
 * Send messages to Groq with streaming.
 * Yields each chunk as a string.
 *
 * @param {Array<{role: string, content: string}>} messages
 * @param {{apiKey?: string, model?: string}} options
 * @returns {AsyncIterable<string>}
 */
export async function* streamGroq(messages, options = {}) {
  const apiKey = options.apiKey || process.env.GROQ_API_KEY;
  if (!apiKey) {
    throw new Error('[Groq] GROQ_API_KEY is not set');
  }

  const model = options.model || DEFAULT_MODEL;
  console.log(`[Groq] Streaming model: ${model}`);

  const client = new Groq({ apiKey });

  const completion = await client.chat.completions.create({
    model,
    messages,
    temperature: DEFAULT_TEMPERATURE,
    max_completion_tokens: DEFAULT_MAX_TOKENS,
    top_p: 0.95,
    stream: true,
  });

  for await (const chunk of completion) {
    const delta = chunk.choices?.[0]?.delta?.content;
    if (delta) {
      yield delta;
    }
  }
}

export { DEFAULT_MODEL as GROQ_MODEL };
