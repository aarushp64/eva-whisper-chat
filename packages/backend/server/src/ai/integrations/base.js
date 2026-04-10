/**
 * Integration Base — standard interface for external connectors
 *
 * Phase 3: All integration modules (social, productivity, media) must
 * implement this interface. Provides a uniform contract for auth,
 * execution, and status across all external services.
 *
 * Interface:
 *   name: string
 *   auth(state) → Promise<{ authenticated: boolean, token?: string }>
 *   execute(action, config) → Promise<{ success: boolean, result?: any, error?: string }>
 *   getStatus() → Promise<{ connected: boolean, ready: boolean }>
 *   disconnect() → Promise<void>
 */

/**
 * Base class for integration connectors.
 * Extend this class and implement the abstract methods.
 */
export class IntegrationBase {
  /**
   * Human-readable name for this integration.
   * @type {string}
   */
  name = 'base';

  /**
   * @type {string|null}
   * @protected
   */
  _apiToken = null;

  /**
   * @type {boolean}
   * @protected
   */
  _isConnected = false;

  /**
   * Authenticate with the external service.
   * Called before any execute() call. If the integration requires
   * OAuth or multi-step auth, the `state` parameter carries the
   * callback data.
   *
   * @param {object} [state] — auth callback data (OAuth code, token, etc.)
   * @returns {Promise<{ authenticated: boolean, token?: string, error?: string }>}
   */
  async auth(state) {
    // Default: check if we have a token from env or previous auth
    const token = process.env[`${this.name.toUpperCase()}_API_KEY`];
    if (token) {
      this._apiToken = token;
      this._isConnected = true;
      return { authenticated: true, token };
    }
    return { authenticated: false, error: `No credentials configured for ${this.name}` };
  }

  /**
   * Execute an action through the external service.
   * Must be overridden by subclasses.
   *
   * @param {string} action — action identifier (e.g., 'post_tweet', 'create_event')
   * @param {object} config — action parameters
   * @returns {Promise<{ success: boolean, result?: any, error?: string }>}
   */
  async execute(action, config) {
    return {
      success: false,
      error: `${this.name} integration not implemented — ${action}(${JSON.stringify(config)})`,
    };
  }

  /**
   * Check connection and readiness status.
   *
   * @returns {Promise<{ connected: boolean, ready: boolean, details?: string }>}
   */
  async getStatus() {
    return {
      connected: this._isConnected,
      ready: this._isConnected && !!this._apiToken,
    };
  }

  /**
   * Disconnect and clear credentials.
   *
   * @returns {Promise<void>}
   */
  async disconnect() {
    this._apiToken = null;
    this._isConnected = false;
    console.log(`[Integration:${this.name}] Disconnected`);
  }

  /**
   * Get the current auth token (for internal use only — never expose to frontend).
   * @returns {string|null}
   */
  get token() {
    return this._apiToken;
  }
}
