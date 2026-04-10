/**
 * Tool Registry — Formal tool contract with JSON Schema validation & risk levels
 *
 * Phase 2: Every tool must conform to:
 *   {
 *     name: string,
 *     description: string,
 *     parameters: { type: 'object', properties: {}, required: string[] },
 *     risk_level: 'low' | 'high',
 *     execute: (input) => Promise<{ success: boolean, result: any } | { success: false, error: string }>,
 *   }
 *
 * Tools are validated against their JSON Schema before execution.
 * High-risk tools are flagged for human-in-the-loop approval.
 */

// ─── Imports (all at top to avoid circular dep issues) ────────────────

import { readFileTool } from './fileTool.js';
import { writeFileTool } from './fileTool.js';
import { shellTool } from './shellTool.js';
import { searchTool } from './searchTool.js';
import { webTool } from './webTool.js';

// ─── Internal registry state ──────────────────────────────────────────

/** @type {Map<string, object>} */
const toolRegistry = new Map();

// ─── Schema Validator ─────────────────────────────────────────────────

/**
 * Lightweight JSON Schema validator (no external dependency).
 * Supports: type (string, number, integer, boolean, object, array),
 * required fields, and basic format checks.
 *
 * @param {object} data — the input to validate
 * @param {object} schema — JSON Schema-like object
 * @param {string[]} required — list of required property names
 * @returns {{ valid: boolean, errors: string[] }}
 */
function validateSchema(data, schema, required = []) {
  const errors = [];

  if (!data || typeof data !== 'object') {
    errors.push('Input must be an object');
    return { valid: false, errors };
  }

  // Check required fields
  for (const field of required) {
    if (!(field in data)) {
      errors.push(`Missing required field: "${field}"`);
    }
  }

  // Check property types
  if (schema.properties) {
    for (const [key, propSchema] of Object.entries(schema.properties)) {
      if (key in data && data[key] !== undefined && data[key] !== null) {
        const value = data[key];
        const expectedType = propSchema.type;

        if (expectedType === 'string' && typeof value !== 'string') {
          errors.push(`Field "${key}" must be a string, got ${typeof value}`);
        } else if (expectedType === 'number' && typeof value !== 'number') {
          errors.push(`Field "${key}" must be a number, got ${typeof value}`);
        } else if (expectedType === 'integer' && (!Number.isInteger(value))) {
          errors.push(`Field "${key}" must be an integer, got ${typeof value}`);
        } else if (expectedType === 'boolean' && typeof value !== 'boolean') {
          errors.push(`Field "${key}" must be a boolean, got ${typeof value}`);
        } else if (expectedType === 'array' && !Array.isArray(value)) {
          errors.push(`Field "${key}" must be an array, got ${typeof value}`);
        } else if (expectedType === 'object' && (typeof value !== 'object' || Array.isArray(value))) {
          errors.push(`Field "${key}" must be an object, got ${Array.isArray(value) ? 'array' : typeof value}`);
        }

        if (expectedType === 'string' && propSchema.minLength && typeof value === 'string') {
          if (value.length < propSchema.minLength) {
            errors.push(`Field "${key}" must be at least ${propSchema.minLength} characters`);
          }
        }

        if (expectedType === 'string' && propSchema.enum && typeof value === 'string') {
          if (!propSchema.enum.includes(value)) {
            errors.push(`Field "${key}" must be one of: ${propSchema.enum.join(', ')}`);
          }
        }

        if (expectedType === 'number' && typeof value === 'number') {
          if (propSchema.minimum !== undefined && value < propSchema.minimum) {
            errors.push(`Field "${key}" must be >= ${propSchema.minimum}`);
          }
          if (propSchema.maximum !== undefined && value > propSchema.maximum) {
            errors.push(`Field "${key}" must be <= ${propSchema.maximum}`);
          }
        }
      }
    }
  }

  return { valid: errors.length === 0, errors };
}

// ─── Public API ───────────────────────────────────────────────────────

/**
 * Register a tool. Validates the tool contract before registration.
 *
 * @param {object} toolDef — tool definition object
 * @param {string} toolDef.name
 * @param {string} toolDef.description
 * @param {object} toolDef.parameters — JSON Schema for input validation
 * @param {'low' | 'high'} toolDef.risk_level
 * @param {function} toolDef.execute
 * @returns {{ success: boolean, error?: string }}
 */
export function registerTool(toolDef) {
  const errors = [];

  if (!toolDef.name || typeof toolDef.name !== 'string') {
    errors.push('Tool must have a "name" string');
  }
  if (!toolDef.description || typeof toolDef.description !== 'string') {
    errors.push('Tool must have a "description" string');
  }
  if (typeof toolDef.execute !== 'function') {
    errors.push('Tool must have an "execute" function');
  }
  if (!['low', 'high'].includes(toolDef.risk_level)) {
    errors.push(`Tool risk_level must be "low" or "high", got "${toolDef.risk_level}"`);
  }
  if (!toolDef.parameters || typeof toolDef.parameters !== 'object') {
    errors.push('Tool must have a "parameters" object (JSON Schema)');
  }

  if (errors.length > 0) {
    console.error(`[Registry] Failed to register tool "${toolDef.name || 'unknown'}":`, errors);
    return { success: false, errors };
  }

  toolRegistry.set(toolDef.name, toolDef);
  console.log(`[Registry] Registered tool: ${toolDef.name} (risk: ${toolDef.risk_level})`);
  return { success: true };
}

/**
 * Get the full tool registry instance.
 *
 * @returns {{ registerTool, getTool, findTool, listTools, validateToolInput, getToolsForPrompt, getHighRiskTools }}
 */
export function getToolRegistry() {
  return {
    registerTool,
    getTool: (name) => toolRegistry.get(name),
    findTool: (name) => toolRegistry.get(name),
    listTools: () => Array.from(toolRegistry.values()),
    validateToolInput,
    getToolsForPrompt,
    getHighRiskTools: () => Array.from(toolRegistry.values()).filter(t => t.risk_level === 'high'),
  };
}

/**
 * Validate tool input against its JSON Schema.
 *
 * @param {string} toolName
 * @param {object} input
 * @returns {{ valid: boolean, errors: string[] }}
 */
export function validateToolInput(toolName, input) {
  const tool = toolRegistry.get(toolName);
  if (!tool) {
    return { valid: false, errors: [`Unknown tool: "${toolName}"`] };
  }

  const schema = tool.parameters || { type: 'object', properties: {} };
  const required = schema.required || [];

  return validateSchema(input, schema, required);
}

/**
 * Execute a tool by name, with pre-execution schema validation.
 *
 * @param {string} toolName
 * @param {object} input
 * @returns {Promise<{ success: boolean, result?: any, error?: string, tool: string }>}
 */
export async function executeTool(toolName, input) {
  const tool = toolRegistry.get(toolName);
  if (!tool) {
    return { success: false, error: `Unknown tool: "${toolName}"`, tool: toolName };
  }

  const validation = validateToolInput(toolName, input);
  if (!validation.valid) {
    console.error(`[Registry] Tool "${toolName}" input validation failed:`, validation.errors);
    return { success: false, error: `Input validation failed: ${validation.errors.join('; ')}`, tool: toolName };
  }

  try {
    const result = await tool.execute(input);
    return { success: true, result, tool: toolName };
  } catch (err) {
    return { success: false, error: err.message, tool: toolName };
  }
}

/**
 * Generate a formatted tool description for LLM prompts.
 * Includes risk level indicators.
 *
 * @returns {string}
 */
export function getToolsForPrompt() {
  const tools = Array.from(toolRegistry.values());
  if (tools.length === 0) return 'No tools available.';

  return tools.map(t => {
    const riskBadge = t.risk_level === 'high' ? ' ⚠️ HIGH-RISK' : '';
    const params = t.parameters?.properties
      ? Object.entries(t.parameters.properties)
          .map(([key, val]) => `${key}: ${val.type}${t.parameters.required?.includes(key) ? ' (required)' : ''}`)
          .join(', ')
      : '(no parameters)';
    return `- ${t.name}(${params}): ${t.description}${riskBadge}`;
  }).join('\n');
}

/**
 * Check if any tool in the plan requires human approval.
 *
 * @param {Array<{ tool?: string }>} steps
 * @returns {Array<{ stepId: string, tool: string, description: string, input: object }>}
 */
export function getPendingApprovals(steps) {
  const approvals = [];
  for (const step of steps) {
    if (!step.tool) continue;
    const tool = toolRegistry.get(step.tool);
    if (tool && tool.risk_level === 'high') {
      approvals.push({
        stepId: step.id,
        tool: step.tool,
        description: step.description,
        input: step.input,
      });
    }
  }
  return approvals;
}

/**
 * Legacy getToolDescriptions alias for backward compatibility.
 * @returns {string}
 */
export const getToolDescriptions = getToolsForPrompt;

// ─── Register built-in tools (at bottom, after functions are defined) ─

registerTool({
  ...readFileTool,
  risk_level: 'low',
  parameters: {
    type: 'object',
    properties: {
      path: { type: 'string', description: 'Absolute or relative file path to read', minLength: 1 },
    },
    required: ['path'],
  },
});

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

registerTool({
  ...shellTool,
  risk_level: 'high',
  parameters: {
    type: 'object',
    properties: {
      command: { type: 'string', description: 'Shell command to execute', minLength: 1 },
    },
    required: ['command'],
  },
});

registerTool({
  ...searchTool,
  risk_level: 'low',
  parameters: {
    type: 'object',
    properties: {
      pattern: { type: 'string', description: 'Filename pattern to search for', minLength: 1 },
      directory: { type: 'string', description: 'Directory to search in (optional)', minLength: 1 },
    },
    required: ['pattern'],
  },
});

registerTool({
  ...webTool,
  risk_level: 'low',
  parameters: {
    type: 'object',
    properties: {
      url: { type: 'string', description: 'URL to fetch and read', minLength: 1 },
    },
    required: ['url'],
  },
});
