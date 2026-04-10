/**
 * Social Media Integration — scaffolding for Phase 3
 *
 * TODO: Implement actual API calls for each platform.
 * Current: Safe mock returns — never calls external APIs.
 *
 * Supported platforms (planned): Twitter/X, Instagram, LinkedIn, Reddit
 *
 * Auth handoff point: Set TWITTER_API_KEY, INSTAGRAM_ACCESS_TOKEN, etc.
 * in .env or call auth({ provider, code }) for OAuth flow.
 */

import { IntegrationBase } from './base.js';

export class SocialIntegration extends IntegrationBase {
  name = 'social';

  /**
   * @param {{ provider: string, code?: string, token?: string }} state
   */
  async auth(state) {
    // TODO: Implement OAuth flow for each platform
    // Twitter/X: OAuth 1.0a → exchange code for token
    // Instagram: OAuth 2.0 → access token
    // LinkedIn: OAuth 2.0 → access token
    // Reddit: OAuth 2.0 → access token

    const envKey = process.env[`${(state.provider || 'SOCIAL').toUpperCase()}_API_KEY`];
    if (envKey || state?.token) {
      this._apiToken = state?.token || envKey;
      this._isConnected = true;
      return { authenticated: true, token: this._apiToken };
    }

    return {
      authenticated: false,
      error: `Social integration requires ${state?.provider || 'an'} API key. Set ${state?.provider || 'SOCIAL'}_API_KEY in .env.`,
    };
  }

  async execute(action, config) {
    // TODO: Route action to the appropriate platform API
    // Actions: 'post_tweet', 'post_instagram', 'post_linkedin', 'get_mentions', 'get_analytics'
    console.log(`[Integration:Social] MOCK — ${action} called with:`, config);
    return {
      success: false,
      error: `Social integration not implemented yet. Action: ${action}`,
    };
  }
}

// Singleton export
export const socialIntegration = new SocialIntegration();
