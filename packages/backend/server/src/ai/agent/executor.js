/**
 * Executor — executes individual plan steps by matching them to tools
 *
 * For each step, the executor asks the LLM whether a tool is needed.
 * If the LLM responds with a tool call JSON, the tool is executed.
 * Otherwise, the LLM's natural language response is returned.
 */

import { routePrompt } from '../router.js';
import { tools, getToolDescriptions, findTool } from '../tools/index.js';

/**
 * Execute a single step from the plan.
 * The LLM decides whether to use a tool or answer directly.
 *
 * @param {string} step — the step description
 * @param {string} [context] — optional context from previous steps
 * @param {{provider?: string, model?: string, apiKey?: string}} [llmConfig]
 * @returns {Promise<string>} — the result of executing this step
 */
export async function executeStep(step, context = '', llmConfig) {
  console.log(`[Executor] Executing step: "${step.slice(0, 80)}"`);

  const systemPrompt = `You are an AI executor. Complete the given step.

Available tools:
${getToolDescriptions()}

If you need a tool, respond with ONLY a JSON object (no extra text):
{"action": "tool_name", "input": { ... }}

If no tool is needed, respond with your answer directly.
Do NOT wrap JSON in markdown code blocks.`;

  const userContent = context
    ? `Context from previous steps:\n${context}\n\nCurrent step to execute:\n${step}`
    : step;

  const messages = [
    { role: 'system', content: systemPrompt },
    { role: 'user', content: userContent },
  ];

  try {
    const response = await routePrompt(messages, llmConfig);

    // Check if the LLM wants to call a tool
    try {
      const parsed = JSON.parse(response.trim());

      if (parsed.action && typeof parsed.action === 'string') {
        const tool = findTool(parsed.action);

        if (tool) {
          console.log(`[Executor] Using tool: ${tool.name}`);
          const result = await tool.execute(parsed.input || {});
          console.log(`[Executor] Tool result: ${String(result).slice(0, 200)}`);
          return `[Tool: ${tool.name}] ${result}`;
        } else {
          console.warn(`[Executor] Unknown tool "${parsed.action}", using LLM response`);
        }
      }
    } catch {
      // Not JSON — natural language response, which is fine
    }

    return response;
  } catch (err) {
    console.error(`[Executor] Step failed: ${err.message}`);

    // Fallback: try to answer with a simpler prompt
    try {
      console.log('[Executor] Falling back to simple LLM response');
      const fallback = await routePrompt(
        [{ role: 'user', content: step }],
        llmConfig
      );
      return fallback;
    } catch (fallbackErr) {
      return `Step failed: ${err.message}`;
    }
  }
}
