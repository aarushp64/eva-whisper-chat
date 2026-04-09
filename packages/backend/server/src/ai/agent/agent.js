/**
 * Agent — main orchestrator for the agentic assistant
 *
 * Flow: Input → Intent Detection → Route by intent:
 *   CHAT   → direct LLM response via routePrompt
 *   TASK   → planner → executor (multi-step)
 *   ACTION → executor (single step, tool-first)
 *   SEARCH → direct LLM response with search context
 *
 * The original runAgent() tool-loop is preserved for backward compatibility.
 */

import { routePrompt } from '../router.js';
import { detectIntent } from '../intent.js';
import { createPlan } from './planner.js';
import { executeStep } from './executor.js';
import { addMessage, getMemory } from '../memory.js';
import { tools, getToolDescriptions } from '../tools/index.js';

const MAX_AGENT_STEPS = 5;

// ─── Main entry point ───────────────────────────────────────────────

/**
 * Run the full assistant pipeline:
 * intent detection → planning → execution → response
 *
 * @param {string} input — the user's message
 * @param {{provider?: string, model?: string, apiKey?: string}} [llmConfig] — runtime LLM config
 * @returns {Promise<string>} — the final response
 */
export async function runAssistant(input, llmConfig) {
  console.log(`\n${'═'.repeat(60)}`);
  console.log(`[Assistant] Input: "${input.slice(0, 100)}"`);
  if (llmConfig) {
    console.log(`[Assistant] LLM Config: ${llmConfig.provider}/${llmConfig.model || 'default'}`);
  }

  const intent = detectIntent(input);
  console.log(`[Assistant] Intent: ${intent}`);

  try {
    switch (intent) {
      case 'CHAT':
        return await handleChat(input, llmConfig);

      case 'TASK':
        return await handleTask(input, llmConfig);

      case 'ACTION':
        return await handleAction(input, llmConfig);

      case 'SEARCH':
        return await handleSearch(input, llmConfig);

      default:
        return await handleChat(input, llmConfig);
    }
  } catch (err) {
    console.error(`[Assistant] Error:`, err.message);
    // Final fallback — simple LLM call
    try {
      return await routePrompt([{ role: 'user', content: input }], llmConfig);
    } catch {
      return 'I apologize, but I encountered an issue processing your request. Please try again.';
    }
  }
}

// ─── Intent handlers ────────────────────────────────────────────────

/**
 * CHAT — simple conversational response, includes memory for context.
 */
async function handleChat(input, llmConfig) {
  console.log('[Assistant] Handling as CHAT');

  const memory = getMemory();
  const messages = [
    { role: 'system', content: 'You are EVA, a friendly and helpful AI assistant. Be concise and natural.' },
    ...memory,
    { role: 'user', content: input },
  ];

  return await routePrompt(messages, llmConfig);
}

/**
 * TASK — multi-step workflow. Generate a plan, then execute each step.
 */
async function handleTask(input, llmConfig) {
  console.log('[Assistant] Handling as TASK');

  // Step 1: Generate a plan
  const plan = await createPlan(input, llmConfig);
  console.log(`[Assistant] Plan: ${JSON.stringify(plan.steps)}`);

  // Step 2: Execute each step sequentially, accumulating context
  const results = [];
  let context = '';

  for (let i = 0; i < plan.steps.length; i++) {
    const step = plan.steps[i];
    console.log(`[Assistant] Executing step ${i + 1}/${plan.steps.length}: ${step}`);

    const result = await executeStep(step, context, llmConfig);
    results.push({ step, result });

    // Build context for the next step
    context += `\nStep ${i + 1} (${step}): ${result}`;
  }

  // Step 3: Summarize results into a final response
  const summaryMessages = [
    {
      role: 'system',
      content: 'You are EVA. Summarize the results of a completed multi-step task. Be clear and concise. Present the key outcomes.',
    },
    {
      role: 'user',
      content: `Original request: ${input}\n\nExecution results:\n${results.map((r, i) => `Step ${i + 1}: ${r.step}\nResult: ${r.result}`).join('\n\n')}`,
    },
  ];

  return await routePrompt(summaryMessages, llmConfig);
}

/**
 * ACTION — single direct action, attempt tool execution first.
 */
async function handleAction(input, llmConfig) {
  console.log('[Assistant] Handling as ACTION');
  return await executeStep(input, '', llmConfig);
}

/**
 * SEARCH — information lookup, answered by the LLM with search context.
 */
async function handleSearch(input, llmConfig) {
  console.log('[Assistant] Handling as SEARCH');

  const memory = getMemory();
  const messages = [
    {
      role: 'system',
      content: `You are EVA, a knowledgeable AI assistant.
Answer the user's question thoroughly but concisely.
If the question is about files or code, suggest using tools in your next response.`,
    },
    ...memory,
    { role: 'user', content: input },
  ];

  return await routePrompt(messages, llmConfig);
}

// ─── Legacy agent loop (preserved for backward compatibility) ───────

/**
 * Run the original tool-calling agent loop.
 * Kept for cases where direct tool-loop iteration is preferred.
 *
 * @param {string} userInput
 * @param {{provider?: string, model?: string, apiKey?: string}} [llmConfig]
 * @returns {Promise<string>}
 */
export async function runAgent(userInput, llmConfig) {
  let context = userInput;
  let steps = 0;

  console.log(`[AgentLoop] Starting for: "${userInput.slice(0, 80)}"`);

  while (steps < MAX_AGENT_STEPS) {
    const messages = [
      {
        role: 'system',
        content: `You are EVA, an AI assistant with tool access.

Available tools:
${getToolDescriptions()}

If you need a tool, respond with ONLY JSON: {"action": "tool_name", "input": { ... }}
Otherwise respond normally. No markdown code blocks around JSON.`,
      },
      { role: 'user', content: context },
    ];

    const response = await routePrompt(messages, llmConfig);

    try {
      const parsed = JSON.parse(response.trim());
      if (parsed.action && typeof parsed.action === 'string') {
        const tool = tools.find(t => t.name === parsed.action);
        if (tool) {
          console.log(`[AgentLoop] Step ${steps + 1}: tool "${tool.name}"`);
          const result = await tool.execute(parsed.input || {});
          context = `Previous request: ${userInput}\n\nTool "${tool.name}" returned:\n${result}\n\nContinue helping the user.`;
          steps++;
          continue;
        }
      }
    } catch {
      // Natural language response
    }

    console.log(`[AgentLoop] Done in ${steps + 1} step(s)`);
    return response;
  }

  return 'Max reasoning steps reached. Please ask a follow-up for more help.';
}
