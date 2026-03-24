/**
 * Web Tool — fetch URL content for the agent loop
 */

import https from 'https';
import http from 'http';

const MAX_BODY_LENGTH = 10000; // Truncate large responses
const TIMEOUT_MS = 15_000;     // 15 second timeout

/**
 * Simple fetch that works without external dependencies.
 * Returns the response body as a string.
 */
function fetchUrl(url) {
  return new Promise((resolve, reject) => {
    const client = url.startsWith('https') ? https : http;

    const req = client.get(url, { timeout: TIMEOUT_MS }, (res) => {
      // Follow redirects (one level)
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        return fetchUrl(res.headers.location).then(resolve).catch(reject);
      }

      let body = '';
      res.setEncoding('utf-8');

      res.on('data', (chunk) => {
        body += chunk;
        if (body.length > MAX_BODY_LENGTH) {
          res.destroy();
        }
      });

      res.on('end', () => resolve(body.slice(0, MAX_BODY_LENGTH)));
      res.on('error', reject);
    });

    req.on('timeout', () => {
      req.destroy();
      reject(new Error('Request timed out'));
    });

    req.on('error', reject);
  });
}

/**
 * Strip HTML tags and collapse whitespace for readability.
 */
function stripHtml(html) {
  return html
    .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
    .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

export const webTool = {
  name: 'fetch_url',
  description: 'Fetch content from a URL and return the text (HTML tags stripped)',
  execute: async ({ url }) => {
    try {
      if (!url || typeof url !== 'string') {
        return 'Error: URL is required';
      }
      console.log(`[WebTool] Fetching: ${url}`);
      const raw = await fetchUrl(url);
      const text = stripHtml(raw);
      return text || '(empty response)';
    } catch (err) {
      return `Error fetching URL: ${err.message}`;
    }
  },
};
