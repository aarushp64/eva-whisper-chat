/**
 * File Write Tool — Write content to a file with risk-level enforcement
 *
 * Phase 2: This tool is marked as HIGH risk and requires human-in-the-loop
 * approval before execution. The execute function is the same as the legacy
 * writeFileTool, but this file exports the full tool definition with schema.
 */

import fs from 'fs/promises';
import path from 'path';

/**
 * Security: Block writing to sensitive system paths.
 * This is enforced at the tool level regardless of approval.
 */
const BLOCKED_PATH_PREFIXES = [
  '/etc/', '/usr/bin/', '/usr/sbin/', '/System/',
  'C:\\Windows\\', 'C:\\Program Files\\', 'C:\\ProgramData\\',
  '/proc/', '/dev/', '/sys/',
  '.env', '.git', 'node_modules',
];

/**
 * Check if a path is safe for writing.
 *
 * @param {string} filePath
 * @returns {{ safe: boolean, reason?: string }}
 */
function isPathSafe(filePath) {
  const resolved = path.resolve(filePath).toLowerCase();

  for (const prefix of BLOCKED_PATH_PREFIXES) {
    if (resolved.includes(prefix.toLowerCase())) {
      return { safe: false, reason: `Writing to "${prefix}" is blocked for security` };
    }
  }

  return { safe: true };
}

/**
 * File Write Tool — high-risk tool requiring approval.
 *
 * Contract:
 *   name: 'write_file'
 *   risk_level: 'high'
 *   parameters: { path (string, required), content (string, required) }
 *   execute: writes file, returns success/error message
 */
export const fileWriteTool = {
  name: 'write_file',
  description: 'Write content to a file at the given path. Creates parent directories if needed.',

  risk_level: 'high',

  parameters: {
    type: 'object',
    properties: {
      path: {
        type: 'string',
        description: 'Absolute or relative file path to write to',
        minLength: 1,
      },
      content: {
        type: 'string',
        description: 'Text content to write',
        minLength: 1,
      },
    },
    required: ['path', 'content'],
  },

  /**
   * Execute the file write. Includes path safety check.
   *
   * @param {{ path: string, content: string }} input
   * @returns {Promise<{ success: boolean, result?: string, error?: string }>}
   */
  execute: async ({ path: filePath, content }) => {
    // Security: block dangerous paths
    const pathCheck = isPathSafe(filePath);
    if (!pathCheck.safe) {
      return { success: false, error: pathCheck.reason };
    }

    try {
      const resolved = path.resolve(filePath);

      // Ensure parent directory exists
      await fs.mkdir(path.dirname(resolved), { recursive: true });

      // Write the file
      await fs.writeFile(resolved, content, 'utf-8');

      return { success: true, result: `File written successfully: ${resolved}` };
    } catch (err) {
      return { success: false, error: `Write error: ${err.message}` };
    }
  },
};

/**
 * Generate a human-readable approval prompt for this tool execution.
 * Used by the executor when risk_level === 'high'.
 *
 * @param {{ path: string, content: string }} input
 * @returns {string}
 */
export function generateApprovalPrompt(input) {
  const truncatedContent = input.content.length > 500
    ? input.content.slice(0, 500) + '...'
    : input.content;

  return `⚠️ High-risk action pending: Write to file

  Path: ${input.path}
  Content (${input.content.length} chars):
  ─────────────────────────────────────
  ${truncatedContent}
  ─────────────────────────────────────

  Type "approve" to proceed or "reject" to cancel.`;
}
