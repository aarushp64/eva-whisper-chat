/**
 * Productivity Integration — scaffolding for Phase 3
 *
 * TODO: Implement actual API calls for each service.
 * Current: Safe mock returns — never calls external APIs.
 *
 * Supported services (planned): Google Calendar, Gmail, Notion, Todoist
 *
 * Auth handoff point: Set GOOGLE_CREDENTIALS, NOTION_API_KEY, etc.
 * in .env or call auth({ provider, code }) for OAuth flow.
 */

import { IntegrationBase } from './base.js';

export class ProductivityIntegration extends IntegrationBase {
  name = 'productivity';

  /**
   * @param {{ provider: string, code?: string, token?: string }} state
   */
  async auth(state) {
    // TODO: Implement OAuth/service-specific auth
    // Google: Service account JSON or OAuth 2.0
    // Notion: OAuth 2.0 or internal integration token
    // Todoist: OAuth 2.0 or sync token

    const envKey = process.env[`${(state.provider || 'PRODUCTIVITY').toUpperCase()}_API_KEY`];
    if (envKey || state?.token) {
      this._apiToken = state?.token || envKey;
      this._isConnected = true;
      return { authenticated: true, token: this._apiToken };
    }

    return {
      authenticated: false,
      error: `Productivity integration requires ${state?.provider || 'a'} API key. Set ${state?.provider || 'PRODUCTIVITY'}_API_KEY in .env.`,
    };
  }

  async execute(action, config) {
    // TODO: Route action to the appropriate service API
    // Actions: 'create_event', 'send_email', 'create_task', 'search_notes', 'get_schedule'
    console.log(`[Integration:Productivity] MOCK — ${action} called with:`, config);
    return {
      success: false,
      error: `Productivity integration not implemented yet. Action: ${action}`,
    };
  }
}

// Singleton export
export const productivityIntegration = new ProductivityIntegration();
