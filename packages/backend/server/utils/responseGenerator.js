/**
 * Response Generator — bridges messageController.js to the AI agent system
 *
 * Phase 2: Supports HITL approval flow. When the agent returns a
 * pending_approval object, this layer passes it through to the
 * messageController as a structured socket event.
 *
 * Routes through: memory → runAssistant (intent → planner → executor → models)
 * Accepts optional runtime LLM config + approval result from the frontend via socket data.
 */

import { routePrompt } from '../src/ai/router.js';
import { addMessage, getMemory } from '../src/ai/memory.js';
import { runAssistant, runAgent } from '../src/ai/agent/agent.js';

// AGENT_MODE controls the processing pipeline:
//   'full'   → intent detection + planner + executor (default)
//   'simple' → legacy tool-calling agent loop
//   'direct' → straight LLM routing, no agent
const AGENT_MODE = process.env.AGENT_MODE || 'full';

/**
 * Generate an AI response for the user's message.
 * Called by messageController.js handleMessage().
 *
 * @param {string} content — the user's message text
 * @param {object|null} userPreference — user preferences from DB
 * @param {string} sentiment — detected message sentiment
 * @param {boolean} isGroupChat — whether this is a group conversation
 * @param {{
 *   provider?: string, model?: string, apiKey?: string,
 *   approvalResult?: { sessionId: string, approved: boolean }
 * }} [llmConfig] — runtime LLM config + optional HITL approval
 * @returns {Promise<string | { isApproval: boolean, response: string, pendingApproval?: object, sessionId?: string }>}
 */
export async function generateResponse(content, userPreference, sentiment, isGroupChat, llmConfig) {
  try {
    const approvalResult = llmConfig?.approvalResult;

    // If resuming from HITL, don't add to memory again (already stored)
    if (!approvalResult) {
      addMessage('user', content);
    }

    let response;

    if (AGENT_MODE === 'direct' || AGENT_MODE === 'false') {
      // Direct routing — no agent, just LLM
      console.log('[ResponseGenerator] Mode: direct routing');
      const systemPrompt = buildSystemPrompt(userPreference, sentiment, isGroupChat);
      const memory = getMemory();
      const messages = [
        { role: 'system', content: systemPrompt },
        ...memory.slice(0, -1),
        { role: 'user', content },
      ];
      response = await routePrompt(messages, llmConfig);

    } else if (AGENT_MODE === 'simple') {
      // Legacy agent loop — tool-calling iteration
      console.log('[ResponseGenerator] Mode: simple agent loop');
      response = await runAgent(content, llmConfig);

    } else {
      // Full assistant — intent → planner → executor
      console.log('[ResponseGenerator] Mode: full assistant');
      response = await runAssistant(content, llmConfig);
    }

    // ── HITL: pass approval objects through unchanged ──
    if (response && typeof response === 'object' && response.pendingApproval) {
      console.log('[ResponseGenerator] HITL approval pending — forwarding to frontend');
      return {
        isApproval: true,
        response: response.response || 'An action requires your approval.',
        pendingApproval: response.pendingApproval,
        sessionId: response.sessionId,
      };
    }

    // Normal string response — store in memory
    if (typeof response === 'string' && !approvalResult) {
      addMessage('assistant', response);
    }

    return response;
  } catch (err) {
    console.error('[ResponseGenerator] Error:', err.message);
    return 'I encountered an issue processing your request. Please try again.';
  }
}

/**
 * Build a system prompt with user preferences and context.
 */
function buildSystemPrompt(userPreference, sentiment, isGroupChat) {
  let prompt = `You are EVA, an empathetic and intelligent virtual assistant.
You are helpful, concise, and friendly. You adapt your tone to the user.`;

  if (sentiment && sentiment !== 'neutral') {
    prompt += `\nThe user's current mood seems ${sentiment}. Be especially ${sentiment === 'negative' ? 'supportive and understanding' : 'enthusiastic and encouraging'}.`;
  }

  if (isGroupChat) {
    prompt += `\nThis is a group conversation. Keep responses concise and address the group naturally.`;
  }

  if (userPreference?.preferredName) {
    prompt += `\nThe user prefers to be called "${userPreference.preferredName}".`;
  }

  return prompt;
}
