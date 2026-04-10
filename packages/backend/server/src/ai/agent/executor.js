/**
 * Executor — executes plan steps with tool matching, HITL approval gate,
 * and hardened error handling (timeout, max iterations, error classification).
 *
 * Phase 2: Handles structured plans from planner.js. For each step:
 *   1. Resolve the tool from the registry
 *   2. Validate input against JSON Schema
 *   3. Check risk_level — if 'high', return pending_approval (no execution)
 *   4. Execute with timeout guard
 *   5. Classify errors (transient vs permanent) for retry decisions
 *
 * The executor can be called in two modes:
 *   - Synchronous (default): executes all low-risk steps, returns pending approvals
 *   - Resume: called with an approval result to continue from a halted state
 */

import { routePrompt } from '../router.js';
import { getToolRegistry, getToolsForPrompt } from '../tools/registry.js';

// ─── Configuration ────────────────────────────────────────────────────

const DEFAULT_MAX_ITERATIONS = 5;
const DEFAULT_TIMEOUT_MS = 30_000; // 30 seconds per tool execution

// ─── Approval session store (in-memory, short-lived) ──────────────────

/**
 * Stores pending approval sessions.
 * Key: sessionId (UUID-like string), Value: execution state snapshot
 *
 * Survives one socket round-trip. Auto-cleans after 5 minutes.
 * @type {Map<string, { plan: object, stepIndex: number, results: Array, context: string, llmConfig?: object, createdAt: number }>}
 */
const approvalSessions = new Map();

const SESSION_TTL_MS = 5 * 60 * 1000; // 5 minutes

/**
 * Clean expired sessions (called periodically or on demand).
 */
export function cleanExpiredSessions() {
  const now = Date.now();
  for (const [id, session] of approvalSessions) {
    if (now - session.createdAt > SESSION_TTL_MS) {
      approvalSessions.delete(id);
      console.log(`[Executor] Expired session: ${id}`);
    }
  }
}

/**
 * Create a new approval session and return its ID.
 *
 * @param {object} executionState
 * @returns {string} sessionId
 */
export function createApprovalSession(executionState) {
  const sessionId = `approval_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
  approvalSessions.set(sessionId, {
    ...executionState,
    createdAt: Date.now(),
  });
  console.log(`[Executor] Created approval session: ${sessionId}`);
  return sessionId;
}

/**
 * Get and consume an approval session (one-shot).
 *
 * @param {string} sessionId
 * @returns {object | null}
 */
export function consumeApprovalSession(sessionId) {
  const session = approvalSessions.get(sessionId);
  if (session) {
    approvalSessions.delete(sessionId); // one-shot consumption
    console.log(`[Executor] Consumed approval session: ${sessionId}`);
  }
  return session || null;
}

// ─── Error Classification ─────────────────────────────────────────────

/**
 * Classify an error as transient (retryable) or permanent (fatal).
 *
 * @param {Error|string} error
 * @returns {{ type: 'transient' | 'permanent', message: string, retryable: boolean }}
 */
export function classifyError(error) {
  const message = typeof error === 'string' ? error : error.message || String(error);
  const lower = message.toLowerCase();

  // Transient errors: network issues, timeouts, rate limits
  const transientPatterns = [
    'timeout', 'econnrefused', 'econnreset', 'enotfound',
    'rate limit', 'too many requests', '429', '503', '502', '504',
    'network', 'fetch failed', 'socket hang up',
  ];

  // Permanent errors: auth failures, not found, invalid input
  const permanentPatterns = [
    'api_key', 'not set', 'unauthorized', '401', '403',
    'validation', 'not found', 'enoent', 'permission denied',
    'eacces', 'unknown tool', 'missing required',
  ];

  for (const pattern of transientPatterns) {
    if (lower.includes(pattern)) {
      return { type: 'transient', message, retryable: true };
    }
  }

  for (const pattern of permanentPatterns) {
    if (lower.includes(pattern)) {
      return { type: 'permanent', message, retryable: false };
    }
  }

  // Default: treat as transient (safer to retry)
  return { type: 'transient', message, retryable: true };
}

// ─── Timeout Guard ────────────────────────────────────────────────────

/**
 * Wrap a promise with a timeout. Rejects if the promise doesn't settle
 * within the specified time.
 *
 * @param {Promise<any>} promise
 * @param {number} timeoutMs
 * @returns {Promise<any>}
 */
function withTimeout(promise, timeoutMs) {
  return Promise.race([
    promise,
    new Promise((_, reject) =>
      setTimeout(() => reject(new Error(`Execution timed out after ${timeoutMs}ms`)), timeoutMs)
    ),
  ]);
}

// ─── Core Execution Engine ───────────────────────────────────────────

/**
 * Execute a single step. Returns the step result or a pending approval request.
 *
 * @param {object} step — { id, description, tool?, input, risk_level }
 * @param {string} context — accumulated context from previous steps
 * @param {{provider?: string, model?: string, apiKey?: string}} [llmConfig]
 * @param {number} [timeoutMs]
 * @returns {Promise<{ status: 'success' | 'pending_approval' | 'error', result?: any, approval?: object, error?: string, step: string }>}
 */
export async function executeStep(step, context = '', llmConfig, timeoutMs = DEFAULT_TIMEOUT_MS) {
  console.log(`[Executor] Executing step: "${step.description.slice(0, 80)}"`);
  console.log(`[Executor] Tool: ${step.tool || 'none'}, Risk: ${step.risk_level}`);

  // If no tool is specified, use the LLM to answer directly
  if (!step.tool) {
    return await executeWithLLM(step, context, llmConfig);
  }

  const registry = getToolRegistry();
  const tool = registry.findTool(step.tool);

  if (!tool) {
    console.warn(`[Executor] Unknown tool "${step.tool}", falling back to LLM`);
    return await executeWithLLM(step, context, llmConfig);
  }

  // ── HITL Gate: block high-risk tools without approval ──
  if (tool.risk_level === 'high' || step.risk_level === 'high') {
    console.log(`[Executor] ⚠️ HITL Gate: "${step.tool}" requires human approval`);
    return {
      status: 'pending_approval',
      step: step.id,
      approval: {
        tool: step.tool,
        description: step.description,
        input: step.input,
        risk_level: 'high',
        prompt: `⚠️ Approval required: Execute "${step.tool}" — ${step.description}`,
      },
    };
  }

  // ── Validate input against JSON Schema ──
  const validation = registry.validateToolInput(step.tool, step.input);
  if (!validation.valid) {
    console.error(`[Executor] Input validation failed for "${step.tool}":`, validation.errors);
    return {
      status: 'error',
      step: step.id,
      error: `Input validation failed: ${validation.errors.join('; ')}`,
      errorType: 'permanent',
    };
  }

  // ── Execute with timeout ──
  try {
    const result = await withTimeout(tool.execute(step.input), timeoutMs);

    // Normalize result: some tools return a string, others { success, result/error }
    const normalizedResult = typeof result === 'string' ? result :
      result.success !== false ? (result.result || JSON.stringify(result)) :
      `Error: ${result.error || 'Unknown error'}`;

    console.log(`[Executor] Tool "${step.tool}" completed: ${String(normalizedResult).slice(0, 200)}`);

    return {
      status: 'success',
      step: step.id,
      result: normalizedResult,
      tool: step.tool,
    };
  } catch (err) {
    const classified = classifyError(err);
    console.error(`[Executor] Step "${step.id}" failed (${classified.type}): ${err.message}`);

    return {
      status: 'error',
      step: step.id,
      error: err.message,
      errorType: classified.type,
      retryable: classified.retryable,
    };
  }
}

/**
 * Execute a step using the LLM directly (no tool).
 * Used when step.tool is null or the tool is unknown.
 *
 * @param {object} step
 * @param {string} context
 * @param {object} [llmConfig]
 * @returns {Promise<{ status: string, result: string, step: string }>}
 */
async function executeWithLLM(step, context, llmConfig) {
  const systemPrompt = `You are EVA. Answer the following request directly.
${context ? `Context from previous steps:\n${context.slice(-2000)}\n\n` : ''}
Request: ${step.description}`;

  try {
    const response = await routePrompt(
      [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: step.description },
      ],
      llmConfig
    );

    return {
      status: 'success',
      step: step.id,
      result: response,
    };
  } catch (err) {
    return {
      status: 'error',
      step: step.id,
      error: `LLM response failed: ${err.message}`,
      errorType: classifyError(err).type,
    };
  }
}

// ─── Plan Executor — runs all steps with HITL and retry logic ─────────

/**
 * Execute an entire plan. Handles max iterations, HITL gates, and error
 * classification. Returns a result object with completed steps, pending
 * approvals, and any errors.
 *
 * @param {{ steps: Array<{id, description, tool?, input, risk_level}> }} plan
 * @param {string} originalInput — the user's original request
 * @param {{provider?: string, model?: string, apiKey?: string}} [llmConfig]
 * @param {{maxIterations?: number, timeoutMs?: number, approvalResult?: { sessionId?: string, approved: boolean } }} [options]
 * @returns {Promise<{
 *   status: 'completed' | 'pending_approval' | 'partial' | 'failed',
 *   results: Array,
 *   pendingApprovals: Array,
 *   sessionId?: string,
 *   summary?: string,
 *   error?: string,
 * }>}
 */
export async function executePlan(plan, originalInput, llmConfig, options = {}) {
  const {
    maxIterations = DEFAULT_MAX_ITERATIONS,
    timeoutMs = DEFAULT_TIMEOUT_MS,
    approvalResult, // { sessionId, approved: boolean } — resume from HITL
  } = options;

  console.log(`\n${'═'.repeat(50)}`);
  console.log(`[Executor] Executing plan: ${plan.steps.length} step(s), max iterations: ${maxIterations}`);

  const results = [];
  const pendingApprovals = [];
  let stepIndex = 0;
  let context = '';
  let consecutiveErrors = 0;

  // ── Resume from approval session ──
  if (approvalResult?.sessionId) {
    const session = consumeApprovalSession(approvalResult.sessionId);
    if (!session) {
      return {
        status: 'failed',
        results: [],
        pendingApprovals: [],
        error: 'Approval session expired or not found. Please resubmit your request.',
      };
    }

    // Restore execution state
    stepIndex = session.stepIndex;
    results.push(...session.results);
    context = session.context;
    llmConfig = session.llmConfig || llmConfig;

    if (!approvalResult.approved) {
      console.log('[Executor] User rejected approval. Halting execution.');
      results.push({
        status: 'rejected',
        step: `step_at_index_${stepIndex}`,
        result: 'Action rejected by user.',
      });
      stepIndex++; // skip the rejected step
    } else {
      console.log('[Executor] User approved. Resuming execution.');
    }
  }

  // ── Execute steps ──
  for (; stepIndex < plan.steps.length; stepIndex++) {
    const step = plan.steps[stepIndex];

    // Check max iterations (count each step attempt as an iteration)
    if (results.length + 1 > maxIterations) {
      console.warn(`[Executor] Max iterations (${maxIterations}) reached at step ${stepIndex + 1}`);
      pendingApprovals.push({
        step: step.id,
        reason: 'Max iterations reached',
        description: step.description,
      });
      break;
    }

    // Execute the step
    const stepResult = await executeStep(step, context, llmConfig, timeoutMs);
    results.push(stepResult);

    if (stepResult.status === 'pending_approval') {
      // HITL: halt and return the approval request
      console.log(`[Executor] Halted at step "${step.id}" — awaiting approval`);

      // Save session for resume
      const sessionId = createApprovalSession({
        plan,
        stepIndex,
        results: [...results],
        context,
        llmConfig,
      });

      return {
        status: 'pending_approval',
        results,
        pendingApprovals: [stepResult.approval],
        sessionId,
      };
    }

    if (stepResult.status === 'success') {
      // Accumulate context for next steps
      context += `\n${step.id} (${step.description}): ${stepResult.result || ''}`;
      consecutiveErrors = 0;
    }

    if (stepResult.status === 'error') {
      consecutiveErrors++;

      // Permanent error → skip and continue (non-blocking)
      // Transient error → retry once
      if (stepResult.retryable && consecutiveErrors <= 2) {
        console.log(`[Executor] Retrying step "${step.id}" (attempt ${consecutiveErrors})`);
        const retryResult = await executeStep(step, context, llmConfig, timeoutMs);
        results.push({ ...retryResult, retry: true });

        if (retryResult.status === 'success') {
          context += `\n${step.id} (retry): ${retryResult.result || ''}`;
          consecutiveErrors = 0;
        }
      }

      if (consecutiveErrors >= 3) {
        console.error('[Executor] Too many consecutive errors. Halting.');
        break;
      }
    }
  }

  // ── All steps completed (or halted) ──
  const completedSteps = results.filter(r => r.status === 'success').length;
  const hasErrors = results.some(r => r.status === 'error');

  if (pendingApprovals.length > 0) {
    return {
      status: 'partial',
      results,
      pendingApprovals,
    };
  }

  // Generate summary via LLM if there were successful steps
  let summary;
  if (completedSteps > 0) {
    try {
      summary = await generateSummary(originalInput, results, llmConfig);
    } catch {
      summary = `Completed ${completedSteps} of ${plan.steps.length} steps.`;
    }
  }

  return {
    status: completedSteps === plan.steps.length ? 'completed' : 'partial',
    results,
    pendingApprovals: [],
    summary: summary || `Completed ${completedSteps} of ${plan.steps.length} steps.`,
  };
}

/**
 * Generate a natural language summary of execution results.
 *
 * @param {string} originalInput
 * @param {Array} results
 * @param {object} [llmConfig]
 * @returns {Promise<string>}
 */
async function generateSummary(originalInput, results, llmConfig) {
  const resultsText = results
    .filter(r => r.status === 'success')
    .map((r, i) => `${i + 1}. ${r.step}: ${r.result || 'Done'}`)
    .join('\n');

  const response = await routePrompt(
    [
      {
        role: 'system',
        content: 'You are EVA. Summarize the results of a completed multi-step task. Be clear and concise. Present the key outcomes in natural language.',
      },
      {
        role: 'user',
        content: `Original request: ${originalInput}\n\nExecution results:\n${resultsText}`,
      },
    ],
    llmConfig
  );

  return response;
}

// ─── Legacy compatibility ─────────────────────────────────────────────

/**
 * Legacy executeStep wrapper — maintains the old string-return interface
 * for backward compatibility with existing callers that don't use plans.
 *
 * @param {string} step — step description
 * @param {string} [context]
 * @param {{provider?: string, model?: string, apiKey?: string}} [llmConfig]
 * @returns {Promise<string>}
 */
export async function executeStepLegacy(step, context = '', llmConfig) {
  const stepObj = {
    id: 'step_1',
    description: step,
    tool: null,
    input: {},
    risk_level: 'low',
  };

  const result = await executeStep(stepObj, context, llmConfig);
  return result.result || result.error || result.approval?.prompt || '(no result)';
}

// ─── Periodic cleanup of expired sessions ─────────────────────────────

setInterval(cleanExpiredSessions, 60 * 1000); // every 60 seconds
