/**
 * Subagent Delegation — specialized agent registry
 *
 * Phase 3: Routes complex tasks to purpose-built subagents when intent
 * confidence is high (> 0.8) and the intent matches a subagent's
 * specialization.
 *
 * Each subagent implements:
 *   canHandle(intentResult) → boolean
 *   delegate(task, llmConfig, sessionId) → Promise<{ output, metadata }>
 *
 * Subagents delegate via JSON contract — never spawn child processes.
 * All execution goes through the existing routePrompt/executor pipeline.
 */

import { routePrompt } from '../router.js';

// ─── Subagent Definitions ─────────────────────────────────────────────

/**
 * CODER Subagent — handles code generation, debugging, refactoring.
 * Uses specialized system prompt with code-aware instructions.
 */
const CODER_SUBAGENT = {
  id: 'CODER',
  label: 'Code Specialist',

  /**
   * @param {{ intent: string, confidence: number, metadata: object }} intentResult
   * @returns {boolean}
   */
  canHandle(intentResult) {
    const codingIntents = ['TASK', 'ACTION'];
    const hasCode = intentResult.metadata?.hasCode;
    const codingKeywords = [
      'function', 'class', 'bug', 'debug', 'error', 'refactor',
      'implement', 'write code', 'script', 'api', 'module',
    ];
    const lower = (intentResult.metadata?.rawInput || '').toLowerCase();
    return (
      codingIntents.includes(intentResult.intent) &&
      intentResult.confidence > 0.7 &&
      (hasCode || codingKeywords.some(kw => lower.includes(kw)))
    );
  },

  /**
   * @param {string} task
   * @param {{provider?: string, model?: string, apiKey?: string}} llmConfig
   * @param {string} sessionId
   * @returns {Promise<{ output: string, metadata: object }>}
   */
  async delegate(task, llmConfig, sessionId) {
    console.log(`[Subagent:CODER] Delegating: "${task.slice(0, 80)}..."`);

    const systemPrompt = `You are EVA's Code Specialist subagent.

Your expertise:
- Writing clean, efficient code in any language
- Debugging and fixing errors
- Refactoring and optimization
- Explaining code architecture and patterns
- Writing tests and documentation

Rules:
- Always provide complete, working code
- Explain your reasoning briefly
- Use best practices for the target language
- If the task is ambiguous, ask clarifying questions
- Include error handling where appropriate`;

    const messages = [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: task },
    ];

    const output = await routePrompt(messages, llmConfig);

    return {
      output,
      metadata: {
        subagent: 'CODER',
        sessionId,
        taskLength: task.length,
      },
    };
  },
};

/**
 * RESEARCHER Subagent — handles information gathering, analysis, summaries.
 */
const RESEARCHER_SUBAGENT = {
  id: 'RESEARCHER',
  label: 'Research Specialist',

  canHandle(intentResult) {
    const researchIntents = ['SEARCH', 'TASK'];
    const researchKeywords = [
      'research', 'analyze', 'compare', 'explain in depth',
      'comprehensive', 'detailed', 'summary of', 'overview of',
      'latest', 'recent developments', 'study',
    ];
    const lower = (intentResult.metadata?.rawInput || '').toLowerCase();
    return (
      researchIntents.includes(intentResult.intent) &&
      intentResult.confidence > 0.7 &&
      researchKeywords.some(kw => lower.includes(kw))
    );
  },

  async delegate(task, llmConfig, sessionId) {
    console.log(`[Subagent:RESEARCHER] Delegating: "${task.slice(0, 80)}..."`);

    const systemPrompt = `You are EVA's Research Specialist subagent.

Your expertise:
- Gathering and synthesizing information
- Comparative analysis
- Identifying key trends and patterns
- Providing balanced, evidence-based summaries
- Citing sources where possible

Rules:
- Be thorough but concise
- Present multiple perspectives when relevant
- Flag uncertainty where it exists
- Structure responses with clear sections
- Prioritize recent, reliable information`;

    const messages = [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: task },
    ];

    const output = await routePrompt(messages, llmConfig);

    return {
      output,
      metadata: {
        subagent: 'RESEARCHER',
        sessionId,
        taskLength: task.length,
      },
    };
  },
};

/**
 * PRODUCTIVITY Subagent — handles scheduling, task management, email drafting.
 */
const PRODUCTIVITY_SUBAGENT = {
  id: 'PRODUCTIVITY',
  label: 'Productivity Specialist',

  canHandle(intentResult) {
    return intentResult.intent === 'PRODUCTIVITY' && intentResult.confidence > 0.7;
  },

  async delegate(task, llmConfig, sessionId) {
    console.log(`[Subagent:PRODUCTIVITY] Delegating: "${task.slice(0, 80)}..."`);

    const systemPrompt = `You are EVA's Productivity Specialist subagent.

Your expertise:
- Task planning and prioritization
- Schedule optimization
- Email drafting and formatting
- Workflow automation suggestions
- Time management strategies

Rules:
- Be action-oriented and specific
- Provide concrete next steps
- Consider time zones and constraints
- Suggest automation where possible
- Keep responses structured and scannable`;

    const messages = [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: task },
    ];

    const output = await routePrompt(messages, llmConfig);

    return {
      output,
      metadata: {
        subagent: 'PRODUCTIVITY',
        sessionId,
        taskLength: task.length,
      },
    };
  },
};

/**
 * MEDIA Subagent — handles image editing, content creation suggestions.
 */
const MEDIA_SUBAGENT = {
  id: 'MEDIA',
  label: 'Media Specialist',

  canHandle(intentResult) {
    return intentResult.intent === 'MEDIA' && intentResult.confidence > 0.7;
  },

  async delegate(task, llmConfig, sessionId) {
    console.log(`[Subagent:MEDIA] Delegating: "${task.slice(0, 80)}..."`);

    const systemPrompt = `You are EVA's Media Specialist subagent.

Your expertise:
- Image editing guidance
- Video/audio processing tips
- Content creation strategy
- Design principles
- File format conversions

Rules:
- Provide step-by-step instructions
- Suggest free/open-source tools first
- Be specific about file formats and settings
- Include quality considerations
- Warn about destructive operations`;

    const messages = [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: task },
    ];

    const output = await routePrompt(messages, llmConfig);

    return {
      output,
      metadata: {
        subagent: 'MEDIA',
        sessionId,
        taskLength: task.length,
      },
    };
  },
};

// ─── Registry & Routing ───────────────────────────────────────────────

/** @type {Array<typeof CODER_SUBAGENT>} */
const SUBAGENTS = [
  CODER_SUBAGENT,
  RESEARCHER_SUBAGENT,
  PRODUCTIVITY_SUBAGENT,
  MEDIA_SUBAGENT,
];

/**
 * Find the best subagent for a given intent.
 * Returns null if no subagent qualifies (falls back to main agent).
 *
 * @param {{ intent: string, confidence: number, metadata: object }} intentResult
 * @returns {typeof CODER_SUBAGENT | null}
 */
export function findSubagent(intentResult) {
  for (const subagent of SUBAGENTS) {
    if (subagent.canHandle(intentResult)) {
      return subagent;
    }
  }
  return null;
}

/**
 * Delegate a task to the best available subagent.
 * Falls back to null if no subagent matches — caller should use main agent.
 *
 * @param {string} task — the task description
 * @param {{provider?: string, model?: string, apiKey?: string}} llmConfig
 * @param {string} sessionId
 * @param {{ intent: string, confidence: number, metadata: object }} intentResult
 * @returns {Promise<{ output: string, metadata: object, delegated: boolean } | null>}
 */
export async function delegateToSubagent(task, llmConfig, sessionId, intentResult) {
  const subagent = findSubagent(intentResult);

  if (!subagent) {
    console.log('[Subagents] No qualifying subagent — using main agent');
    return null;
  }

  try {
    const result = await subagent.delegate(task, llmConfig, sessionId);
    console.log(`[Subagents] ${subagent.id} completed delegation`);
    return {
      ...result,
      delegated: true,
    };
  } catch (err) {
    console.error(`[Subagents] ${subagent.id} delegation failed: ${err.message}`);
    // Fail gracefully — return null so caller falls back to main agent
    return null;
  }
}

/**
 * List all available subagents and their capabilities.
 *
 * @returns {Array<{ id: string, label: string }>}
 */
export function listSubagents() {
  return SUBAGENTS.map(s => ({ id: s.id, label: s.label }));
}
