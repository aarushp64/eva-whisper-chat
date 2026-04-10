/**
 * Planner — breaks a complex task into sequential steps using the LLM
 *
 * Phase 2: Returns structured JSON plan with id, tool mapping, input schema,
 * and risk_level ('low' | 'high') for each step.
 *
 * Accepts the structured intent result from detectIntent() to tailor
 * the planning prompt. Falls back gracefully on parse failures.
 */

import { routePrompt } from '../router.js';
import { getToolRegistry } from '../tools/registry.js';

// Maximum steps the planner is allowed to generate
const MAX_STEPS = 8;

/**
 * Build the system prompt for the planner, incorporating intent and
 * available tool information to guide realistic step generation.
 *
 * @param {object} intentResult — { intent, confidence, metadata }
 * @returns {string}
 */
function buildPlannerPrompt(intentResult) {
  const registry = getToolRegistry();
  const toolList = registry.listTools();

  const toolDescriptions = toolList.map(t => {
    const params = t.parameters
      ? Object.entries(t.parameters.properties)
          .map(([key, val]) => `  - ${key}: ${val.type}${val.required ? ' (required)' : ''}`)
          .join('\n')
      : '  (no parameters)';
    return `- ${t.name}: ${t.description}\n  Risk: ${t.risk_level}\n${params}`;
  }).join('\n');

  const intent = intentResult?.intent || 'TASK';
  const metadata = intentResult?.metadata || {};

  let contextHints = '';
  if (metadata.paths?.length) contextHints += `\nUser mentioned file paths: ${metadata.paths.join(', ')}`;
  if (metadata.urls?.length) contextHints += `\nUser mentioned URLs: ${metadata.urls.join(', ')}`;
  if (metadata.hasCode) contextHints += '\nUser input contains code blocks.';

  return `You are a task planner for EVA, an AI agent with tool access.
Given a user request, break it into clear, actionable steps.

Available tools (with risk levels):
${toolDescriptions}

Risk levels:
- "low": Read-only or safe operations (read files, search, get time, web fetch)
- "high": Destructive or external operations (write files, run commands, post to social, send emails)

Respond with ONLY a JSON object in this exact format (no markdown, no explanation):
{
  "steps": [
    {
      "id": "step_1",
      "description": "Brief description of what this step does",
      "tool": "tool_name or null if no tool needed",
      "input": { "param": "value" },
      "risk_level": "low" | "high"
    }
  ]
}

Rules:
- Each step must have a unique id like "step_1", "step_2", etc.
- If a step needs a tool, set "tool" to its exact name and "input" to its parameters
- If no tool is needed, set "tool": null and "input": {}
- Mark "risk_level": "high" for write_file, run_command, or any external action
- Maximum ${MAX_STEPS} steps
- Steps must be in logical execution order
- Keep steps concrete and specific${contextHints}

Current intent: ${intent}`;
}

/**
 * Parse the LLM's response into a structured plan.
 * Handles markdown code fences, extra text, and parse failures.
 *
 * @param {string} rawResponse
 * @param {string} fallbackInput — the original user input
 * @returns {{ steps: Array<{id, description, tool?, input, risk_level}> }}
 */
function parsePlan(rawResponse, fallbackInput) {
  let cleaned = rawResponse.trim();

  // Strip markdown code fences if present
  const codeBlockMatch = cleaned.match(/```(?:json)?\s*\n([\s\S]*?)\n```/);
  if (codeBlockMatch) {
    cleaned = codeBlockMatch[1];
  }

  try {
    const parsed = JSON.parse(cleaned);

    if (!parsed.steps || !Array.isArray(parsed.steps) || parsed.steps.length === 0) {
      throw new Error('Plan has no steps array');
    }

    // Normalize each step: ensure required fields
    const steps = parsed.steps.map((step, idx) => ({
      id: step.id || `step_${idx + 1}`,
      description: step.description || `Step ${idx + 1}`,
      tool: step.tool || null,
      input: step.input || {},
      risk_level: ['low', 'high'].includes(step.risk_level) ? step.risk_level : 'low',
    }));

    return { steps };
  } catch (err) {
    console.warn(`[Planner] Failed to parse plan: ${err.message}`);
    console.log('[Planner] Raw response:', rawResponse.slice(0, 300));
    return null;
  }
}

/**
 * Generate a single-step fallback plan from the user's input.
 * Used when the LLM plan fails to parse.
 *
 * @param {string} input
 * @returns {{ steps: Array }}
 */
function createFallbackPlan(input) {
  console.log('[Planner] Falling back to single-step plan');
  return {
    steps: [{
      id: 'step_1',
      description: input,
      tool: null,
      input: {},
      risk_level: 'low',
    }],
  };
}

/**
 * Generate an execution plan for a user's task request.
 *
 * @param {string} input — the user's task description
 * @param {{provider?: string, model?: string, apiKey?: string}} [llmConfig]
 * @param {object} [intentResult] — optional result from detectIntent()
 * @returns {Promise<{steps: Array<{id, description, tool?, input, risk_level}>}>}
 */
export async function createPlan(input, llmConfig, intentResult) {
  console.log('[Planner] Generating plan for:', input.slice(0, 80));

  try {
    const messages = [
      { role: 'system', content: buildPlannerPrompt(intentResult) },
      { role: 'user', content: input },
    ];

    const response = await routePrompt(messages, llmConfig);
    const plan = parsePlan(response, input);

    if (plan) {
      console.log(`[Planner] Created plan with ${plan.steps.length} step(s)`);
      plan.steps.forEach(s => {
        console.log(`  [${s.id}] ${s.description} (tool: ${s.tool || 'none'}, risk: ${s.risk_level})`);
      });
      return plan;
    }

    return createFallbackPlan(input);
  } catch (err) {
    console.error(`[Planner] Planning error: ${err.message}`);
    return createFallbackPlan(input);
  }
}
