/**
 * Tool Registry — Central registry of all available agent tools
 *
 * Each tool exposes: { name, description, execute(input) }
 * The agent/executor uses this registry to find and invoke tools.
 */

import { readFileTool, writeFileTool } from './fileTool.js';
import { shellTool } from './shellTool.js';
import { searchTool } from './searchTool.js';
import { webTool } from './webTool.js';

export const tools = [
  readFileTool,
  writeFileTool,
  shellTool,
  searchTool,
  webTool,
];

/**
 * Find a tool by name.
 * @param {string} name
 * @returns {object | undefined}
 */
export function findTool(name) {
  return tools.find(t => t.name === name);
}

/**
 * Get a formatted description of all tools for the system prompt.
 * @returns {string}
 */
export function getToolDescriptions() {
  return tools.map(t => `- ${t.name}: ${t.description}`).join('\n');
}
