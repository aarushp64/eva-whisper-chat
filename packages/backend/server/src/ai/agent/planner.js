/**
 * Planner — breaks a complex task into sequential steps using the LLM
 *
 * Sends the user's request to the router and asks the model to produce
 * a JSON execution plan. Falls back to a single-step plan if parsing fails.
 */

import { routePrompt } from '../router.js';

const PLANNER_SYSTEM_PROMPT = `You are a task planner. Given a user request, break it into clear, actionable steps.

Respond with ONLY a JSON object in this exact format (no markdown, no explanation):
{"steps": ["step 1 description", "step 2 description", ...]}

Rules:
- Each step should be a single, concrete action
- Keep steps short and specific
- Maximum 8 steps
- If the task is simple, use 1-2 steps
- Steps should be in logical execution order`;

/**
 * Generate an execution plan for a user's task request.
 *
 * @param {string} input — the user's task description
 * @returns {Promise<{steps: string[]}>} — the plan with ordered steps
 */
export async function createPlan(input) {
  console.log('[Planner] Generating plan for:', input.slice(0, 80));

  try {
    const messages = [
      { role: 'system', content: PLANNER_SYSTEM_PROMPT },
      { role: 'user', content: input },
    ];

    const response = await routePrompt(messages);

    // Try to parse the model's response as JSON
    const parsed = JSON.parse(response.trim());

    if (parsed.steps && Array.isArray(parsed.steps) && parsed.steps.length > 0) {
      console.log(`[Planner] Created plan with ${parsed.steps.length} step(s)`);
      return parsed;
    }

    throw new Error('Invalid plan format');
  } catch (err) {
    // Fallback: treat the entire input as a single step
    console.warn(`[Planner] Failed to generate multi-step plan: ${err.message}`);
    console.log('[Planner] Falling back to single-step plan');
    return { steps: [input] };
  }
}
