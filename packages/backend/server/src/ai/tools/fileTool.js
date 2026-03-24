/**
 * File Tool — Read and write files from the agent loop
 */

import fs from 'fs/promises';
import path from 'path';

export const readFileTool = {
  name: 'read_file',
  description: 'Read the contents of a file given its path',
  execute: async ({ path: filePath }) => {
    try {
      const resolved = path.resolve(filePath);
      const data = await fs.readFile(resolved, 'utf-8');
      return data;
    } catch (err) {
      return `Error reading file: ${err.message}`;
    }
  },
};

export const writeFileTool = {
  name: 'write_file',
  description: 'Write content to a file at the given path',
  execute: async ({ path: filePath, content }) => {
    try {
      const resolved = path.resolve(filePath);
      // Ensure directory exists
      await fs.mkdir(path.dirname(resolved), { recursive: true });
      await fs.writeFile(resolved, content, 'utf-8');
      return `File written successfully: ${resolved}`;
    } catch (err) {
      return `Error writing file: ${err.message}`;
    }
  },
};
