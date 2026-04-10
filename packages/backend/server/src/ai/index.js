/**
 * AI Core — Barrel export for the agentic AI pipeline
 *
 * Import from here to keep consumers decoupled from internal structure.
 *
 * Usage:
 *   import { routePrompt, runAssistant, detectIntent } from '@/ai';
 */

// ─── Phase 1: Routing & Providers ─────────────────────────────────────
export { routePrompt, selectProvider } from './router.js';

// ─── Phase 2: Agent Pipeline ──────────────────────────────────────────
export { runAssistant, runAgent } from './agent/agent.js';
export { createPlan } from './agent/planner.js';
export {
  executeStep,
  executePlan,
  executeStepLegacy,
  createApprovalSession,
  consumeApprovalSession,
  cleanExpiredSessions,
  classifyError,
} from './agent/executor.js';

// ─── Phase 2: Intent Detection ────────────────────────────────────────
export { detectIntent } from './intent.js';

// ─── Phase 2: Tools ───────────────────────────────────────────────────
export {
  registerTool,
  getToolRegistry,
  validateToolInput,
  executeTool,
  getToolsForPrompt,
  getPendingApprovals,
  getToolDescriptions,
  findTool,
  tools,
  readFileTool,
  writeFileTool,
  shellTool,
  searchTool,
  webTool,
  fileWriteTool,
  generateApprovalPrompt,
} from './tools/index.js';

// ─── Phase 3: Subagent Delegation ─────────────────────────────────────
export {
  findSubagent,
  delegateToSubagent,
  listSubagents,
} from './agents/subagents.js';

// ─── Phase 3: Review Loop ─────────────────────────────────────────────
export { reviewOutput } from './loop/review.js';

// ─── Phase 3: Semantic Memory ─────────────────────────────────────────
export {
  storeMemory,
  recallMemory,
  clearSessionMemory,
  getMemoryStats,
  initializeVectorStore,
} from './memory/semantic.js';

// ─── Phase 3: Integrations (scaffolding) ──────────────────────────────
export {
  IntegrationBase,
  SocialIntegration,
  socialIntegration,
  ProductivityIntegration,
  productivityIntegration,
  MediaIntegration,
  mediaIntegration,
} from './integrations/index.js';

// ─── Phase 1: Conversation Memory ─────────────────────────────────────
export { addMessage, getMemory, clearMemory } from './memory.js';
