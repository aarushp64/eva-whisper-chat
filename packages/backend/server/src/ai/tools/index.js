/**
 * Tool Index — backward-compatible barrel + re-export from registry
 *
 * Phase 2: Tools are registered in registry.js. This file re-exports
 * from the registry while maintaining the legacy `tools` array export
 * for existing imports like `import { tools, findTool } from './index.js'`.
 *
 * NOTE: No imports FROM this file in registry.js (would cause circular dep).
 */

import { readFileTool, writeFileTool } from './fileTool.js';
import { shellTool } from './shellTool.js';
import { searchTool } from './searchTool.js';
import { webTool } from './webTool.js';
import {
  getToolRegistry,
  registerTool,
  validateToolInput,
  executeTool,
  getPendingApprovals,
  getToolsForPrompt,
  getToolDescriptions,
} from './registry.js';

// Register writeFileTool (registry.js already registered the others)
registerTool({
  ...writeFileTool,
  risk_level: 'high',
  parameters: {
    type: 'object',
    properties: {
      path: { type: 'string', description: 'File path to write to', minLength: 1 },
      content: { type: 'string', description: 'Content to write', minLength: 1 },
    },
    required: ['path', 'content'],
  },
});

// Legacy: flat array of all tool objects (for backward compatibility with
// old code that iterates over the array directly)
export const tools = [
  readFileTool,
  writeFileTool,
  shellTool,
  searchTool,
  webTool,
];

/**
 * Find a tool by name — checks the registry first, then falls back to
 * the legacy array for tools that may not be registered yet.
 * @param {string} name
 * @returns {object | undefined}
 */
export function findTool(name) {
  return getToolRegistry().findTool(name) || tools.find(t => t.name === name);
}

// Re-export registry functions for convenience
export {
  registerTool,
  getToolRegistry,
  validateToolInput,
  executeTool,
  getPendingApprovals,
  getToolsForPrompt,
  getToolDescriptions,
} from './registry.js';

// Re-export individual tools for direct import
export { readFileTool, writeFileTool } from './fileTool.js';
export { shellTool } from './shellTool.js';
export { searchTool } from './searchTool.js';
export { webTool } from './webTool.js';
export { fileWriteTool, generateApprovalPrompt } from './fileWriteTool.js';
