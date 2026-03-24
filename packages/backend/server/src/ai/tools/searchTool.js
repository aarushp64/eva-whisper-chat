/**
 * Search Tool — Search for files by name or content in the project
 */

import fs from 'fs/promises';
import path from 'path';

const MAX_RESULTS = 20;
const IGNORED_DIRS = ['node_modules', '.git', '__pycache__', 'venv', 'dist', '.next'];

/**
 * Recursively search for files matching a pattern.
 */
async function walkDir(dir, pattern, results = []) {
  if (results.length >= MAX_RESULTS) return results;

  try {
    const entries = await fs.readdir(dir, { withFileTypes: true });

    for (const entry of entries) {
      if (results.length >= MAX_RESULTS) break;

      if (IGNORED_DIRS.includes(entry.name)) continue;

      const fullPath = path.join(dir, entry.name);

      if (entry.isDirectory()) {
        await walkDir(fullPath, pattern, results);
      } else if (entry.name.toLowerCase().includes(pattern.toLowerCase())) {
        results.push(fullPath);
      }
    }
  } catch {
    // Skip directories we can't read
  }

  return results;
}

export const searchTool = {
  name: 'search_files',
  description: 'Search for files by name pattern in the project directory',
  execute: async ({ pattern, directory }) => {
    const searchDir = directory || process.cwd();
    try {
      const results = await walkDir(searchDir, pattern);
      if (results.length === 0) return 'No files found matching pattern.';
      return results.join('\n');
    } catch (err) {
      return `Search error: ${err.message}`;
    }
  },
};
