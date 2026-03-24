/**
 * User Profiling — track user emotional state over time
 *
 * Stub implementation. Logs emotional updates for now.
 * Fulfills the import in messageController.js:
 *   import { updateUserEmotionalState } from '../utils/userProfiling.js'
 */

/**
 * Update the user's emotional state based on their latest message.
 * @param {string} userId
 * @param {string} sentiment — 'positive' | 'negative' | 'neutral'
 * @param {string} content — the message content
 */
export async function updateUserEmotionalState(userId, sentiment, content) {
  // Stub: log for observability, expand later with DB persistence
  if (sentiment !== 'neutral') {
    console.log(`[UserProfiling] User ${userId} sentiment: ${sentiment}`);
  }
}
