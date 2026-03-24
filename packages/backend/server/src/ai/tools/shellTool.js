/**
 * Shell Tool — Execute terminal commands from the agent loop
 *
 * WARNING: This runs commands on the host machine.
 * Timeout and output length are capped for safety.
 */

import { exec } from 'child_process';

const MAX_OUTPUT_LENGTH = 5000;  // Truncate long outputs
const TIMEOUT_MS = 30_000;       // 30 second timeout

export const shellTool = {
  name: 'run_command',
  description: 'Execute a terminal/shell command and return its output',
  execute: async ({ command }) => {
    return new Promise((resolve) => {
      exec(command, { timeout: TIMEOUT_MS }, (err, stdout, stderr) => {
        if (err) {
          const output = stderr || err.message;
          resolve(`Command error: ${output.slice(0, MAX_OUTPUT_LENGTH)}`);
          return;
        }
        const result = stdout.slice(0, MAX_OUTPUT_LENGTH);
        resolve(result || '(no output)');
      });
    });
  },
};
