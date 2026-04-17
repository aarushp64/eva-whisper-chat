/**
 * Intent Detection — classify user input into actionable intent categories
 *
 * Phase 2: Returns structured { intent, confidence, metadata } object.
 * Backward-compatible: if called without `structured: true`, returns the
 * legacy string for existing agent.js switch statements.
 *
 * Intents:
 *   CHAT           — conversational, no tool needed
 *   TASK           — multi-step work (create, build, implement)
 *   ACTION         — direct single command (run, open, read file)
 *   SEARCH         — information lookup (search, find, what is)
 *   SOCIAL         — social media action (post, tweet, share, like)
 *   MEDIA          — media manipulation (edit image, crop, convert video)
 *   PRODUCTIVITY   — calendar/email/task management (schedule, remind, send email)
 *   COMMUNICATION  — messaging/calling someone (message, call, notify, ping)
 */

// ─── Keyword sets per intent ──────────────────────────────────────────

const TASK_KEYWORDS = [
  'create', 'build', 'make', 'generate', 'implement', 'set up', 'setup',
  'configure', 'install', 'deploy', 'migrate', 'convert', 'transform',
  'refactor', 'optimize', 'update', 'upgrade', 'add', 'remove', 'delete',
  'fix', 'solve', 'automate', 'write a script', 'write code', 'develop',
  'plan', 'design', 'architect', 'restructure', 'organize',
];

const ACTION_KEYWORDS = [
  'run', 'execute', 'open', 'read file', 'show file',
  'list files', 'cat', 'ls', 'dir', 'pwd', 'cd', 'fetch', 'download',
  'curl', 'ping', 'check status', 'restart', 'stop', 'start',
  'kill', 'npm run', 'node ', 'git ', 'pip ',
];

const SEARCH_KEYWORDS = [
  'search', 'find', 'look for', 'where is', 'locate', 'grep', 'lookup',
  'what is', 'who is', 'how to', 'explain', 'tell me about', 'define',
];

const SOCIAL_KEYWORDS = [
  'post', 'tweet', 'share', 'like', 'comment', 'follow', 'retweet',
  'publish', 'social media', 'instagram', 'twitter', 'facebook', 'linkedin',
  'reddit', 'discord', 'slack message', 'send a message to',
];

const MEDIA_KEYWORDS = [
  'edit image', 'crop', 'resize', 'convert video', 'compress image',
  'extract audio', 'merge pdf', 'generate image', 'create image',
  'photo', 'screenshot', 'transcode', 'render', 'play', 'pause', 'resume'
];

const PRODUCTIVITY_KEYWORDS = [
  'schedule', 'remind', 'reminder', 'calendar', 'send email', 'create task',
  'add to calendar', 'set alarm', 'todo', 'to-do', 'organize my',
  'plan my', 'book a meeting', 'invite', 'event', 'set timer', 'timer'
];

const COMMUNICATION_KEYWORDS = [
  'message', 'call', 'notify', 'ping', 'contact', 'reach out',
  'send a text', 'email', 'dm', 'direct message', 'text', 'call'
];

// Ordered checks: most specific first, least specific (CHAT) as default
const INTENT_CHECKS = [
  { intent: 'SOCIAL',       keywords: SOCIAL_KEYWORDS,       weight: 1.0 },
  { intent: 'MEDIA',        keywords: MEDIA_KEYWORDS,        weight: 1.0 },
  { intent: 'COMMUNICATION', keywords: COMMUNICATION_KEYWORDS, weight: 1.0 },
  { intent: 'PRODUCTIVITY', keywords: PRODUCTIVITY_KEYWORDS, weight: 1.0 },
  { intent: 'ACTION',       keywords: ACTION_KEYWORDS,       weight: 1.0 },
  { intent: 'TASK',         keywords: TASK_KEYWORDS,         weight: 0.9 },
  { intent: 'SEARCH',       keywords: SEARCH_KEYWORDS,       weight: 0.8 },
];

/**
 * Compute a confidence score based on keyword density.
 * More matched keywords → higher confidence.
 */
function computeConfidence(lower, keywords, weight) {
  const matches = keywords.filter(kw => lower.includes(kw)).length;
  if (matches === 0) return 0;
  // Base confidence from match count, capped and weighted
  const raw = Math.min(matches / 2, 1.0); // 1+ matches = 0.5+, 2+ = ~1.0
  return Math.round(raw * weight * 100) / 100;
}

/**
 * Extract metadata from the input for downstream use.
 */
function extractMetadata(input) {
  const lower = input.toLowerCase();
  const metadata = {};

  // Detect file paths
  const pathMatch = input.match(/[\/\\][\w.\/\\-]+/g);
  if (pathMatch) metadata.paths = pathMatch;

  // Detect URLs
  const urlMatch = input.match(/https?:\/\/[^\s]+/g);
  if (urlMatch) metadata.urls = urlMatch;

  // Detect code blocks
  if (input.includes('```') || input.includes('`')) {
    metadata.hasCode = true;
  }

  // Detect numbers (could be quantities, phone numbers, etc.)
  const numbers = input.match(/\b\d+\.?\d*\b/g);
  if (numbers) metadata.numbers = numbers.map(Number);

  // Detect if the input is a question
  metadata.isQuestion = input.trim().endsWith('?');

  return metadata;
}

/**
 * Detect the user's intent from their input text.
 *
 * @param {string} input — the user's message
 * @param {{structured?: boolean}} [options] — if true, return full object
 * @returns {string | {intent: string, confidence: number, metadata: object}}
 */
export function detectIntent(input, options = {}) {
  const lower = input.toLowerCase();
  const structured = options.structured !== false; // default to structured

  let bestIntent = 'CHAT';
  let bestConfidence = 0.3; // baseline for CHAT

  for (const check of INTENT_CHECKS) {
    const conf = computeConfidence(lower, check.keywords, check.weight);
    if (conf > bestConfidence) {
      bestConfidence = conf;
      bestIntent = check.intent;
    }
  }

  const metadata = extractMetadata(input);

  console.log(`[Intent] Detected: ${bestIntent} (confidence: ${bestConfidence})`);

  // Backward-compatible: return plain string for legacy callers
  if (!structured) {
    return bestIntent;
  }

  return {
    intent: bestIntent,
    confidence: bestConfidence,
    metadata,
  };
}
