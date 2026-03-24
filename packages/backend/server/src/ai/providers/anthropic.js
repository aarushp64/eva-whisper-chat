/**
 * Anthropic Provider — Premium fallback via Anthropic Messages API
 * Only used when other providers fail.
 * API key read from process.env.ANTHROPIC_API_KEY
 */

import axios from 'axios';

const ANTHROPIC_URL = 'https://api.anthropic.com/v1/messages';
const ANTHROPIC_MODEL = process.env.ANTHROPIC_MODEL || 'claude-sonnet-4-20250514';

/**
 * Send messages to Anthropic and return the response string.
 * Converts standard chat format to Anthropic's messages API format.
 * @param {Array<{role: string, content: string}>} messages
 * @returns {Promise<string>}
 */
export async function callAnthropic(messages) {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    throw new Error('[Anthropic] ANTHROPIC_API_KEY is not set');
  }

  console.log(`[Anthropic] Calling model: ${ANTHROPIC_MODEL}`);

  // Separate system message from conversation messages
  // Anthropic requires system as a top-level param, not in messages array
  const systemMsg = messages.find(m => m.role === 'system');
  const chatMessages = messages
    .filter(m => m.role !== 'system')
    .map(m => ({
      role: m.role === 'assistant' ? 'assistant' : 'user',
      content: m.content,
    }));

  const response = await axios.post(ANTHROPIC_URL, {
    model: ANTHROPIC_MODEL,
    max_tokens: 4096,
    ...(systemMsg ? { system: systemMsg.content } : {}),
    messages: chatMessages,
  }, {
    headers: {
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
      'Content-Type': 'application/json',
    },
    timeout: 60_000,
  });

  const content = response.data?.content?.[0]?.text;
  if (!content) {
    throw new Error('[Anthropic] Empty response from model');
  }

  return content;
}

export { ANTHROPIC_MODEL };
