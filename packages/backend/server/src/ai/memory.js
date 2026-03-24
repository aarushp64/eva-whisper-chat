/**
 * Memory — Conversation history manager
 *
 * Maintains a rolling window of the last N messages for context continuity.
 * The router prepends this memory to every prompt.
 */

const MAX_MESSAGES = parseInt(process.env.MEMORY_SIZE, 10) || 20;

/** @type {Array<{role: string, content: string}>} */
let conversationHistory = [];

/**
 * Add a message to conversation memory.
 * Automatically trims to MAX_MESSAGES.
 * @param {'user' | 'assistant' | 'system'} role
 * @param {string} content
 */
export function addMessage(role, content) {
  conversationHistory.push({ role, content });

  // Trim from the front to keep recent messages
  if (conversationHistory.length > MAX_MESSAGES) {
    conversationHistory = conversationHistory.slice(-MAX_MESSAGES);
  }
}

/**
 * Get the current conversation memory.
 * @returns {Array<{role: string, content: string}>}
 */
export function getMemory() {
  return [...conversationHistory];
}

/**
 * Clear all conversation memory.
 */
export function clearMemory() {
  conversationHistory = [];
}
