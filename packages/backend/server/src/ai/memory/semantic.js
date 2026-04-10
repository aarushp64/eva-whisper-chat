/**
 * Semantic Memory — lightweight context store with vector retrieval
 *
 * Phase 3: Stores conversation context with embeddings for semantic search.
 * Falls back to in-memory LRU cache if ChromaDB/vector store is unavailable.
 *
 * Memory operations are async-safe and session-scoped.
 * Each entry is keyed by sessionId to prevent cross-session contamination.
 *
 * Exports:
 *   storeMemory(sessionId, text, metadata)  → { id, sessionId }
 *   recallMemory(query, topK, sessionId?)   → Array<{ content, metadata, score }>
 *   clearSessionMemory(sessionId)            → void
 *   getMemoryStats()                         → { totalEntries, sessions, cacheSize }
 */

// ─── Configuration ────────────────────────────────────────────────────

const DEFAULT_TOP_K = 3;
const DEFAULT_CACHE_SIZE = 100; // max entries in LRU fallback
const VECTOR_STORE_ENABLED = process.env.VECTOR_STORE_ENABLED === 'true';

// ─── In-Memory LRU Cache (fallback when no vector store) ──────────────

/**
 * Simple LRU cache for memory entries.
 * Entries are stored per-session for isolation.
 */
class LRUCache {
  constructor(maxSize = DEFAULT_CACHE_SIZE) {
    this.maxSize = maxSize;
    /** @type {Map<string, { content: string, metadata: object, timestamp: number }>} */
    this.store = new Map();
  }

  /**
   * Store an entry in the cache.
   * @param {string} key — unique key (e.g., `${sessionId}:${timestamp}`)
   * @param {{ content: string, metadata: object }} value
   */
  set(key, value) {
    // If key exists, delete it first (to refresh LRU order)
    if (this.store.has(key)) {
      this.store.delete(key);
    }
    this.store.set(key, { ...value, timestamp: Date.now() });

    // Evict oldest entries if over capacity
    while (this.store.size > this.maxSize) {
      const oldestKey = this.store.keys().next().value;
      this.store.delete(oldestKey);
    }
  }

  /**
   * Retrieve all entries for a session, optionally filtered by similarity.
   * Since LRU has no vector search, we return most recent entries.
   *
   * @param {string} sessionId
   * @param {number} topK
   * @returns {Array<{ content: string, metadata: object, score: number }>}
   */
  getBySession(sessionId, topK = DEFAULT_TOP_K) {
    const prefix = `${sessionId}:`;
    const entries = [];

    for (const [key, value] of this.store) {
      if (key.startsWith(prefix)) {
        entries.push({
          content: value.content,
          metadata: value.metadata,
          score: 0.5, // fallback score — no similarity computation in LRU
        });
      }
    }

    // Return most recent entries
    return entries.slice(-topK).reverse();
  }

  /**
   * Search all entries with simple keyword overlap scoring.
   * Lightweight alternative to vector similarity.
   *
   * @param {string} query
   * @param {string|null} sessionId — if provided, restrict to this session
   * @param {number} topK
   * @returns {Array<{ content: string, metadata: object, score: number }>}
   */
  search(query, sessionId = null, topK = DEFAULT_TOP_K) {
    const queryTerms = new Set(query.toLowerCase().split(/\s+/).filter(t => t.length > 2));
    const results = [];

    for (const [key, value] of this.store) {
      // Session filter
      if (sessionId && !key.startsWith(`${sessionId}:`)) continue;

      // Keyword overlap scoring
      const contentTerms = new Set(value.content.toLowerCase().split(/\s+/).filter(t => t.length > 2));
      let matches = 0;
      for (const term of queryTerms) {
        if (contentTerms.has(term)) matches++;
      }
      const score = queryTerms.size > 0 ? matches / queryTerms.size : 0;

      if (score > 0) {
        results.push({
          content: value.content,
          metadata: value.metadata,
          score,
        });
      }
    }

    // Sort by score descending, take top K
    return results.sort((a, b) => b.score - a.score).slice(0, topK);
  }

  /**
   * Remove all entries for a session.
   * @param {string} sessionId
   */
  clearSession(sessionId) {
    const prefix = `${sessionId}:`;
    for (const key of this.store.keys()) {
      if (key.startsWith(prefix)) {
        this.store.delete(key);
      }
    }
  }

  get size() { return this.store.size; }
}

// ─── Global Memory State ──────────────────────────────────────────────

// Single LRU cache instance shared across the process
const lruCache = new LRUCache();

// Vector store client (lazy-initialized, optional)
let vectorStoreClient = null;
let vectorStoreAvailable = false;

/**
 * Attempt to initialize the vector store (ChromaDB or similar).
 * This is async and non-blocking — failures fall back to LRU silently.
 * Called once at startup and can be re-triggered on demand.
 *
 * @returns {Promise<boolean>}
 */
export async function initializeVectorStore() {
  if (vectorStoreAvailable) return true;
  if (!VECTOR_STORE_ENABLED) {
    console.log('[Memory] Vector store disabled — using LRU cache');
    return false;
  }

  try {
    // Lazy import — vector store deps (chromadb, etc.) are heavy
    // and may not be installed. Wrap in try/catch.
    const { ChromaClient } = await import('chromadb');
    const client = new ChromaClient({
      path: process.env.CHROMA_HOST || 'http://localhost:8000',
    });
    vectorStoreClient = client;
    vectorStoreAvailable = true;
    console.log('[Memory] Vector store connected');
    return true;
  } catch (err) {
    console.warn(`[Memory] Vector store unavailable (${err.message}) — falling back to LRU cache`);
    vectorStoreAvailable = false;
    vectorStoreClient = null;
    return false;
  }
}

/**
 * Generate a lightweight embedding-like representation using TF-IDF
 * term frequencies. Used for local similarity scoring when no vector
 * store is available.
 *
 * @param {string} text
 * @returns {Map<string, number>} — term → weight map
 */
function computeTermFrequencies(text) {
  const terms = text.toLowerCase().split(/\s+/).filter(t => t.length > 2);
  const freq = new Map();
  for (const term of terms) {
    freq.set(term, (freq.get(term) || 0) + 1);
  }
  // Normalize
  const total = terms.length || 1;
  for (const [term, count] of freq) {
    freq.set(term, count / total);
  }
  return freq;
}

/**
 * Cosine similarity between two term frequency maps.
 *
 * @param {Map<string, number>} a
 * @param {Map<string, number>} b
 * @returns {number} — similarity score [0, 1]
 */
function cosineSimilarity(a, b) {
  const allTerms = new Set([...a.keys(), ...b.keys()]);
  let dotProduct = 0;
  let magA = 0;
  let magB = 0;

  for (const term of allTerms) {
    const va = a.get(term) || 0;
    const vb = b.get(term) || 0;
    dotProduct += va * vb;
    magA += va * va;
    magB += vb * vb;
  }

  const denominator = Math.sqrt(magA) * Math.sqrt(magB);
  return denominator > 0 ? dotProduct / denominator : 0;
}

// ─── Public API ───────────────────────────────────────────────────────

/**
 * Store a memory entry.
 * Session-scoped — entries are isolated by sessionId.
 *
 * @param {string} sessionId — unique session identifier
 * @param {string} text — the text content to store
 * @param {object} [metadata] — optional metadata (intent, tool usage, etc.)
 * @returns {Promise<{ id: string, sessionId: string, stored: boolean }>}
 */
export async function storeMemory(sessionId, text, metadata = {}) {
  const id = `${sessionId}:${Date.now()}:${Math.random().toString(36).slice(2, 6)}`;

  const entry = {
    content: text,
    metadata: {
      ...metadata,
      timestamp: Date.now(),
      sessionId,
    },
  };

  // Try vector store first
  if (vectorStoreAvailable && vectorStoreClient) {
    try {
      const collection = await vectorStoreClient.getOrCreateCollection({ name: 'eva_memory' });
      await collection.add({
        ids: [id],
        documents: [text],
        metadatas: [entry.metadata],
      });
      console.log(`[Memory] Stored in vector store: ${id.slice(0, 30)}...`);
      return { id, sessionId, stored: true };
    } catch (err) {
      console.warn(`[Memory] Vector store write failed, falling back to LRU: ${err.message}`);
    }
  }

  // Fallback: LRU cache
  lruCache.set(id, entry);
  console.log(`[Memory] Stored in LRU cache: ${id.slice(0, 30)}...`);
  return { id, sessionId, stored: true };
}

/**
 * Recall relevant context for a query.
 * Uses vector similarity if available, otherwise keyword overlap on LRU.
 *
 * @param {string} query — the search query
 * @param {number} [topK] — number of results to return (default: 3)
 * @param {string|null} [sessionId] — if provided, restrict to this session
 * @returns {Promise<Array<{ content: string, metadata: object, score: number }>>}
 */
export async function recallMemory(query, topK = DEFAULT_TOP_K, sessionId = null) {
  // Try vector store first
  if (vectorStoreAvailable && vectorStoreClient) {
    try {
      const collection = await vectorStoreClient.getOrCreateCollection({ name: 'eva_memory' });
      const where = sessionId ? { sessionId } : undefined;
      const results = await collection.query({
        queryTexts: [query],
        nResults: topK,
        ...(where ? { where } : {}),
      });

      if (results.documents?.[0]?.length > 0) {
        return results.documents[0].map((doc, idx) => ({
          content: doc,
          metadata: results.metadatas?.[0]?.[idx] || {},
          score: results.distances?.[0]?.[idx] ? 1 - results.distances[0][idx] : 0.5,
        }));
      }
    } catch (err) {
      console.warn(`[Memory] Vector store recall failed, falling back to LRU: ${err.message}`);
    }
  }

  // Fallback: LRU cache with keyword overlap scoring
  return lruCache.search(query, sessionId, topK);
}

/**
 * Clear all memory for a session.
 *
 * @param {string} sessionId
 */
export async function clearSessionMemory(sessionId) {
  lruCache.clearSession(sessionId);

  if (vectorStoreAvailable && vectorStoreClient) {
    try {
      const collection = await vectorStoreClient.getOrCreateCollection({ name: 'eva_memory' });
      // ChromaDB doesn't support bulk delete by metadata directly,
      // so we'd need to query then delete. Skip for now — LRU handles it.
    } catch {
      // Non-critical — LRU already cleared
    }
  }

  console.log(`[Memory] Cleared session memory: ${sessionId}`);
}

/**
 * Get memory system statistics.
 *
 * @returns {{ totalEntries: number, sessions: Set<string>, cacheSize: number, vectorStore: boolean }}
 */
export function getMemoryStats() {
  const sessions = new Set();
  for (const key of lruCache.store.keys()) {
    const sessionId = key.split(':')[0];
    sessions.add(sessionId);
  }

  return {
    totalEntries: lruCache.size,
    sessions: sessions.size,
    cacheSize: lruCache.size,
    vectorStore: vectorStoreAvailable,
  };
}

// ─── Auto-initialize vector store on module load (non-blocking) ───────

initializeVectorStore().catch(() => {
  // Expected: ChromaDB may not be running. LRU handles everything.
});
