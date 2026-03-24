/**
 * Sentiment Analysis — analyze user message sentiment
 *
 * Uses the 'sentiment' npm package (already in dependencies).
 * Fulfills the import in messageController.js:
 *   import { analyzeUserSentiment } from '../utils/sentimentAnalysis.js'
 */

import Sentiment from 'sentiment';

const analyzer = new Sentiment();

/**
 * Analyze the sentiment of a text message.
 * @param {string} text
 * @returns {Promise<'positive' | 'negative' | 'neutral'>}
 */
export async function analyzeUserSentiment(text) {
  try {
    const result = analyzer.analyze(text);

    if (result.score > 1) return 'positive';
    if (result.score < -1) return 'negative';
    return 'neutral';
  } catch (err) {
    console.warn('[Sentiment] Analysis failed, defaulting to neutral:', err.message);
    return 'neutral';
  }
}
