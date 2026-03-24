/**
 * Memory Manager — extract and store key information from messages
 *
 * Stub implementation. Logs for now.
 * Fulfills the import in messageController.js:
 *   import { extractKeyInformation } from '../utils/memoryManager.js'
 */

/**
 * Extract key information from a user's message for long-term memory.
 * @param {string} userId
 * @param {string} content — the message content
 */
export async function extractKeyInformation(userId, content) {
  // Stub: will be expanded to use NLP extraction + DB storage
  // For now, just log messages that seem important (names, preferences, etc.)
  const importanceKeywords = ['my name is', 'i prefer', 'remember that', 'i like', 'i hate'];
  const lower = content.toLowerCase();

  if (importanceKeywords.some(kw => lower.includes(kw))) {
    console.log(`[MemoryManager] Key info detected from user ${userId}: "${content.slice(0, 100)}"`);
  }
}
