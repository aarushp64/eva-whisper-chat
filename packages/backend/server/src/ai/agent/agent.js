/**
 * Agent — main orchestrator for the agentic assistant
 *
 * Phase 3 Pipeline:
 *   Input → Intent Detection (structured)
 *         → Subagent Delegation (if confidence > 0.8 + matching specialization)
 *         → Planner (multi-step breakdown)
 *         → Executor (tool execution + HITL gate)
 *         → Review Loop (self-correction)
 *         → Semantic Memory Store
 *         → Final Response
 *
 * HITL: High-risk steps return pending_approval. Caller resumes with
 *       { approvalResult: { sessionId, approved } }.
 *
 * Backward compatible: runAgent() legacy loop preserved.
 * Streaming and llmConfig threading intact.
 */

import { routePrompt } from '../router.js';
import { detectIntent } from '../intent.js';
import { createPlan } from './planner.js';
import { executePlan, executeStepLegacy, consumeApprovalSession } from './executor.js';
import { delegateToSubagent, findSubagent } from '../agents/subagents.js';
import { reviewOutput } from '../loop/review.js';
import { storeMemory, recallMemory } from '../memory/semantic.js';
import { addMessage, getMemory } from '../memory.js';
import { getToolsForPrompt } from '../tools/index.js';
import { gateway } from '../gateway/bridge.js';
import { checkProactiveSuggestions, capturePreferences } from '../behaviors/proactive.js';
import * as GoogleCalendar from '../integrations/google_calendar.js';

// ─── Configuration ────────────────────────────────────────────────────

const MAX_AGENT_STEPS = 5;

// Intents that trigger the full planner → executor pipeline
const PLANNED_INTENTS = new Set([
  'TASK', 'ACTION', 'SOCIAL', 'MEDIA', 'PRODUCTIVITY', 'COMMUNICATION',
]);

// Intents that skip subagent delegation (handled directly)
const DIRECT_INTENTS = new Set(['CHAT', 'SEARCH']);

// ─── Session ID Generation ────────────────────────────────────────────

/**
 * Generate a unique session ID for memory scoping.
 * @returns {string}
 */
function generateSessionId() {
  return `sess_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

// ─── Main Entry Point ─────────────────────────────────────────────────

/**
 * Run the full assistant pipeline with Phase 3 agentic flow.
 *
 * @param {string} input — the user's message
 * @param {{
 *   provider?: string,
 *   model?: string,
 *   apiKey?: string,
 *   approvalResult?: { sessionId: string, approved: boolean },
 *   sessionId?: string — override auto-generated session ID
 * }} [options] — LLM config + optional HITL approval resume
 * @returns {Promise<string | { response: string, pendingApproval?: object, sessionId?: string }>}
 */
export async function runAssistant(input, options) {
  // Support legacy call signature: runAssistant(input, llmConfig)
  const llmConfig = options && !options.provider && !options.approvalResult && !options.sessionId
    ? options
    : options || {};
  const approvalResult = options?.approvalResult;
  const sessionId = options?.sessionId || generateSessionId();

  console.log(`\n${'═'.repeat(60)}`);
  console.log(`[Assistant] Input: "${input.slice(0, 100)}"`);
  console.log(`[Assistant] Session: ${sessionId}`);
  if (llmConfig?.provider) {
    console.log(`[Assistant] LLM Config: ${llmConfig.provider}/${llmConfig.model || 'default'}`);
  }
  if (approvalResult) {
    console.log(`[Assistant] Resuming approval session: ${approvalResult.sessionId} (approved: ${approvalResult.approved})`);
  }

  // ── Resume from HITL approval (Phase 2) ──
  if (approvalResult?.sessionId) {
    return await resumeFromApproval(input, approvalResult, llmConfig, sessionId);
  }

  // ── Phase 1: Structured Intent Detection ──
  const intentResult = detectIntent(input, { structured: true });
  // Attach raw input for subagent keyword matching
  intentResult.metadata.rawInput = input;
  console.log(`[Assistant] Intent: ${intentResult.intent} (confidence: ${intentResult.confidence})`);

  // ── Phase 4: Proactive Memory Catch ──
  await capturePreferences(sessionId, input);
  const suggestion = checkProactiveSuggestions([intentResult]);

  // ── Phase 4: Heavy Offloading (Gateway) ──
  let extraContext = '';
  if (intentResult.intent === 'SEARCH' && intentResult.confidence > 0.9) {
    const gatewayRes = await gateway.dispatch('HEAVY_RAG', { query: input });
    if (!gatewayRes?._gateway_fallback) extraContext = gatewayRes;
  }

  // ── Recall relevant context from semantic memory ──
  let memoryContext = '';
  try {
    const memories = await recallMemory(input, 3, sessionId);
    if (memories.length > 0) {
      memoryContext = '\nRelevant past context:\n' +
        memories.map(m => `- ${m.content} (score: ${m.score.toFixed(2)})`).join('\n');
      console.log(`[Assistant] Recalled ${memories.length} memory entries`);
    }
    if (extraContext) {
      memoryContext += `\nGateway Knowledge:\n${JSON.stringify(extraContext)}`;
    }
  } catch {
    // Memory recall is non-blocking
  }

  try {
    let responseText = '';
    // Route based on intent type
    switch (intentResult.intent) {
      case 'CHAT':
      case 'SEARCH':
        responseText = await handleChatLike(input, intentResult, llmConfig, sessionId, memoryContext);
        break;

      case 'TASK':
      case 'ACTION':
      case 'SOCIAL':
      case 'MEDIA':
      case 'PRODUCTIVITY':
      case 'COMMUNICATION':
        responseText = await handlePlannedTask(input, intentResult, llmConfig, sessionId, memoryContext);
        break;

      default:
        responseText = await handleChatLike(input, intentResult, llmConfig, sessionId, memoryContext);
    }
    
    // Proactive Response Attachment
    if (typeof responseText === 'string' && suggestion) {
      return `${responseText}\n\n*Voice Assistant Suggestion: ${suggestion}*`;
    }
    return responseText;
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

// ─── HITL Resume (Phase 2, preserved) ─────────────────────────────────

/**
 * Resume plan execution after user approves/rejects a high-risk action.
 *
 * @param {string} _input — original input
 * @param {{ sessionId: string, approved: boolean }} approvalResult
 * @param {object} [llmConfig]
 * @param {string} sessionId
 * @returns {Promise<string | object>}
 */
async function resumeFromApproval(_input, approvalResult, llmConfig, sessionId) {
  const session = consumeApprovalSession(approvalResult.sessionId);

  if (!session) {
    console.warn('[Assistant] Approval session expired. Requesting fresh input.');
    return 'Your approval session expired. Please resubmit your original request.';
  }

  console.log(`[Assistant] Resuming plan execution (approved: ${approvalResult.approved})`);

  const result = await executePlan(session.plan, _input, llmConfig, {
    approvalResult,
  });

  if (result.status === 'pending_approval') {
    return {
      response: 'Another action requires your approval.',
      pendingApproval: result.pendingApprovals?.[0],
      sessionId: result.sessionId,
    };
  }

  // Phase 3: Review the resumed output
  const rawOutput = result.summary || result.results.map(r => r.result).filter(Boolean).join('\n');
  const reviewed = await reviewOutput(_input, rawOutput, llmConfig);

  // Store in memory
  await storeMemory(sessionId, reviewed.finalOutput, {
    intent: 'resumed_task',
    toolUsage: result.results,
  });

  return reviewed.finalOutput;
}

// ─── Intent Handlers ──────────────────────────────────────────────────

/**
 * CHAT / SEARCH — direct LLM response with memory context.
 *
 * @param {string} input
 * @param {object} intentResult
 * @param {object} [llmConfig]
 * @param {string} sessionId
 * @param {string} memoryContext
 * @returns {Promise<string>}
 */
async function handleChatLike(input, intentResult, llmConfig, sessionId, memoryContext) {
  const isSearch = intentResult.intent === 'SEARCH';
  console.log(`[Assistant] Handling as ${intentResult.intent}`);

  const memory = getMemory();

  const systemContent = isSearch
    ? `You are EVA, a knowledgeable AI assistant.
Answer the user's question thoroughly but concisely.${memoryContext}`
    : `You are EVA, a friendly and helpful AI assistant. Be concise and natural.${memoryContext}`;

  const messages = [
    { role: 'system', content: systemContent },
    ...memory,
    { role: 'user', content: input },
  ];

  const response = await routePrompt(messages, llmConfig);

  // Phase 3: Store interaction in semantic memory
  await storeMemory(sessionId, `User: ${input}\nEVA: ${response}`, {
    intent: intentResult.intent,
    confidence: intentResult.confidence,
  });

  return response;
}

/**
 * TASK / ACTION / SOCIAL / MEDIA / PRODUCTIVITY / COMMUNICATION
 *
 * Phase 3 Pipeline:
 *   1. Subagent Delegation (if confidence > 0.8 + match)
 *   2. Planner (structured step breakdown)
 *   3. Executor (tool execution + HITL gate)
 *   4. Review Loop (self-correction)
 *   5. Semantic Memory Store
 *
 * @param {string} input
 * @param {object} intentResult
 * @param {object} [llmConfig]
 * @param {string} sessionId
 * @param {string} memoryContext
 * @returns {Promise<string | { response: string, pendingApproval: object, sessionId: string }>}
 */
async function handlePlannedTask(input, intentResult, llmConfig, sessionId, memoryContext) {
  console.log(`[Assistant] Handling as ${intentResult.intent}`);

  // ── Phase 3 Step 1: Subagent Delegation ──
  const subagentResult = await delegateToSubagent(input, llmConfig, sessionId, intentResult);

  if (subagentResult?.delegated) {
    console.log(`[Assistant] Delegated to subagent: ${subagentResult.metadata.subagent}`);

    // Phase 3 Step 4: Review subagent output
    const reviewed = await reviewOutput(input, subagentResult.output, llmConfig);

    // Phase 3 Step 5: Store in semantic memory
    await storeMemory(sessionId, `User: ${input}\nEVA (${subagentResult.metadata.subagent}): ${reviewed.finalOutput}`, {
      intent: intentResult.intent,
      confidence: intentResult.confidence,
      subagent: subagentResult.metadata.subagent,
    });

    return reviewed.finalOutput;
  }

  // ── Phase 3 Step 2: Planner (structured breakdown) ──
  console.log('[Assistant] Planning multi-step task...');
  const plan = await createPlan(input, llmConfig, intentResult);

  // ── Phase 3 Step 3: Executor (with HITL support) ──
  const result = await executePlan(plan, input, llmConfig, {
    maxIterations: MAX_AGENT_STEPS,
  });

  // ── Handle HITL pending approval ──
  if (result.status === 'pending_approval') {
    console.log(`[Assistant] Plan halted — awaiting approval for: ${result.pendingApprovals?.[0]?.tool}`);
    return {
      response: result.pendingApprovals?.[0]?.prompt || 'An action requires your approval.',
      pendingApproval: result.pendingApprovals?.[0],
      sessionId: result.sessionId,
    };
  }

  if (result.status === 'failed') {
    return `I was unable to complete your request: ${result.error || 'Unknown error.'}`;
  }

  // ── Phase 3 Step 4: Review Loop ──
  const rawOutput = result.summary || result.results.map(r => r.result).filter(Boolean).join('\n');
  console.log('[Assistant] Running review loop...');
  const reviewed = await reviewOutput(input, rawOutput, llmConfig);

  // ── Phase 3 Step 5: Store in Semantic Memory ──
  await storeMemory(sessionId, `User: ${input}\nEVA: ${reviewed.finalOutput}`, {
    intent: intentResult.intent,
    confidence: intentResult.confidence,
    reviewScore: reviewed.score,
    reviewPassed: reviewed.passed,
    toolResults: result.results.filter(r => r.status === 'success').length,
  });

  console.log(`[Assistant] Plan ${result.status} — review: ${reviewed.passed ? 'passed' : 'corrected'} (score: ${reviewed.score})`);
  return reviewed.finalOutput;
}

// ─── Legacy Agent Loop (Phase 1/2 backward compat) ────────────────────

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

  const toolDescriptions = getToolsForPrompt();

  while (steps < MAX_AGENT_STEPS) {
    const messages = [
      {
        role: 'system',
        content: `You are EVA, an AI assistant with tool access.

Available tools:
${toolDescriptions}

If you need a tool, respond with ONLY JSON: {"action": "tool_name", "input": { ... }}
Otherwise respond normally. No markdown code blocks around JSON.`,
      },
      { role: 'user', content: context },
    ];

    const response = await routePrompt(messages, llmConfig);

    try {
      const parsed = JSON.parse(response.trim());
      if (parsed.action && typeof parsed.action === 'string') {
        const toolName = parsed.action;
        const input = parsed.input || {};

        const stepResult = await executeStepLegacy(
          `${toolName} with input: ${JSON.stringify(input)}`,
          context,
          llmConfig
        );

        if (stepResult.includes('Approval required') || stepResult.includes('⚠️')) {
          console.log(`[AgentLoop] HITL gate triggered for tool "${toolName}"`);
          return stepResult;
        }

        context = `Previous request: ${userInput}\n\nTool "${toolName}" returned:\n${stepResult}\n\nContinue helping the user.`;
        steps++;
        continue;
      }
    } catch {
      // Natural language response — done
    }

    console.log(`[AgentLoop] Done in ${steps + 1} step(s)`);
    return response;
  }

  return 'Max reasoning steps reached. Please ask a follow-up for more help.';
}
