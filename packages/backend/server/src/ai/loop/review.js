/**
 * Review/Evaluation Gate — post-execution quality validation
 *
 * Phase 3: Runs after the executor completes steps. Validates output
 * against expected format/schema. If invalid or low-confidence, triggers
 * one self-correction retry via LLM before finalizing.
 *
 * Max retries: 1 (prevents infinite loops)
 * Timeout: 15s per review pass
 * Falls gracefully to raw executor output if LLM review fails
 */

import { routePrompt } from '../router.js';

// ─── Configuration ────────────────────────────────────────────────────

const REVIEW_TIMEOUT_MS = 15_000;
const MAX_RETRIES = 1;
const MIN_PASSING_SCORE = 0.6;

// ─── Review Prompts ───────────────────────────────────────────────────

/**
 * System prompt for the review LLM. Asks it to evaluate the output
 * against quality criteria.
 */
const REVIEW_PROMPT = `You are a quality reviewer for EVA, an AI agent system.

Your task: Evaluate the agent's output against the user's original request.
Score the output from 0.0 to 1.0 based on:

1. COMPLETENESS (30%): Does the output fully address the request?
2. ACCURACY (30%): Is the information correct and relevant?
3. CLARITY (20%): Is the response well-structured and easy to understand?
4. SAFETY (20%): Does the output avoid harmful, misleading, or risky content?

Respond with ONLY a JSON object (no markdown, no explanation):
{
  "passed": true | false,
  "score": 0.0 to 1.0,
  "strengths": ["list of what the output did well"],
  "weaknesses": ["list of what could be improved"],
  "corrections": "specific instructions for improving the output",
  "finalOutput": "the improved output text, or empty if no changes needed"
}

Rules:
- If score >= 0.6, set passed: true
- If passed: true, set corrections: "" and finalOutput: "" (no changes needed)
- If passed: false, provide specific corrections and improved finalOutput
- Be objective and specific in your evaluation`;

/**
 * Self-correction prompt — used when the review identifies issues.
 */
const CORRECTION_PROMPT = (originalRequest, currentOutput, review) => `The following response to a user request was evaluated and found to need improvement.

Original Request:
${originalRequest}

Current Output:
${currentOutput}

Review Feedback:
- Weaknesses: ${review.weaknesses?.join('; ') || 'None specified'}
- Corrections needed: ${review.corrections || 'None specified'}

Please provide an improved version that addresses these issues while maintaining the strengths:
- Strengths: ${review.strengths?.join('; ') || 'None specified'}

Respond with ONLY the improved output text. No preamble, no explanation.`;

// ─── Timeout Guard ────────────────────────────────────────────────────

/**
 * Wrap a promise with a timeout.
 *
 * @param {Promise<any>} promise
 * @param {number} ms
 * @returns {Promise<any>}
 */
function withTimeout(promise, ms) {
  return Promise.race([
    promise,
    new Promise((_, reject) =>
      setTimeout(() => reject(new Error(`Review timed out after ${ms}ms`)), ms)
    ),
  ]);
}

// ─── Review Engine ────────────────────────────────────────────────────

/**
 * Parse the review response from the LLM.
 * Handles malformed JSON gracefully.
 *
 * @param {string} rawResponse
 * @returns {{ passed: boolean, score: number, strengths: string[], weaknesses: string[], corrections: string, finalOutput: string } | null}
 */
function parseReview(rawResponse) {
  let cleaned = rawResponse.trim();

  // Strip markdown code fences
  const codeBlockMatch = cleaned.match(/```(?:json)?\s*\n([\s\S]*?)\n```/);
  if (codeBlockMatch) {
    cleaned = codeBlockMatch[1];
  }

  try {
    const parsed = JSON.parse(cleaned);

    // Validate required fields
    if (typeof parsed.passed !== 'boolean') {
      // Try to infer from score
      const score = typeof parsed.score === 'number' ? parsed.score : 0;
      parsed.passed = score >= MIN_PASSING_SCORE;
    }

    return {
      passed: parsed.passed,
      score: typeof parsed.score === 'number' ? parsed.score : 0,
      strengths: Array.isArray(parsed.strengths) ? parsed.strengths : [],
      weaknesses: Array.isArray(parsed.weaknesses) ? parsed.weaknesses : [],
      corrections: parsed.corrections || '',
      finalOutput: parsed.finalOutput || '',
    };
  } catch {
    console.warn('[Review] Failed to parse LLM review response');
    return null;
  }
}

/**
 * Run a quality review on the agent's output.
 *
 * @param {string} originalRequest — the user's original request
 * @param {string} currentOutput — the agent's generated output
 * @param {{provider?: string, model?: string, apiKey?: string}} [llmConfig]
 * @returns {Promise<{ passed: boolean, score: number, corrections: string, finalOutput: string }>}
 */
export async function reviewOutput(originalRequest, currentOutput, llmConfig) {
  console.log('[Review] Starting quality review...');

  try {
    const reviewMessages = [
      { role: 'system', content: REVIEW_PROMPT },
      { role: 'user', content: `Original Request:\n${originalRequest}\n\nAgent Output:\n${currentOutput}` },
    ];

    const rawReview = await withTimeout(
      routePrompt(reviewMessages, llmConfig),
      REVIEW_TIMEOUT_MS
    );

    const review = parseReview(rawReview);

    if (!review) {
      console.warn('[Review] Parse failed — passing output through without review');
      return {
        passed: true, // fail-open: don't block output if review itself fails
        score: 0,
        corrections: '',
        finalOutput: currentOutput,
      };
    }

    console.log(`[Review] Score: ${review.score} — Passed: ${review.passed}`);

    // ── If review says output needs improvement, trigger one retry ──
    if (!review.passed && review.corrections) {
      console.log('[Review] Triggering self-correction retry...');
      return await runCorrection(originalRequest, currentOutput, review, llmConfig);
    }

    return {
      passed: review.passed,
      score: review.score,
      corrections: review.corrections,
      finalOutput: review.finalOutput || currentOutput,
    };
  } catch (err) {
    console.error(`[Review] Review error: ${err.message}`);
    // Fail-open: return original output if review process fails
    return {
      passed: true,
      score: 0,
      corrections: '',
      finalOutput: currentOutput,
    };
  }
}

/**
 * Run one self-correction cycle.
 *
 * @param {string} originalRequest
 * @param {string} currentOutput
 * @param {object} review
 * @param {object} [llmConfig]
 * @returns {Promise<{ passed: boolean, score: number, corrections: string, finalOutput: string }>}
 */
async function runCorrection(originalRequest, currentOutput, review, llmConfig) {
  try {
    const correctionMessages = [
      {
        role: 'system',
        content: 'You are EVA. Improve your previous response based on the feedback provided. Output only the improved response text.',
      },
      {
        role: 'user',
        content: CORRECTION_PROMPT(originalRequest, currentOutput, review),
      },
    ];

    const correctedOutput = await withTimeout(
      routePrompt(correctionMessages, llmConfig),
      REVIEW_TIMEOUT_MS
    );

    console.log('[Review] Self-correction complete');

    return {
      passed: true, // corrected output is accepted
      score: review.score,
      corrections: review.corrections,
      finalOutput: correctedOutput,
    };
  } catch (err) {
    console.error(`[Review] Correction failed: ${err.message}`);
    // Return original output as fallback
    return {
      passed: true,
      score: review.score,
      corrections: review.corrections,
      finalOutput: currentOutput,
    };
  }
}
