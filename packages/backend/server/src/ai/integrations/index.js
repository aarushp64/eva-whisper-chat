/**
 * Integrations — barrel export for all external connectors
 *
 * Phase 3: Placeholder scaffolding. Each integration implements
 * the IntegrationBase interface and can be enabled via .env config.
 */

export { IntegrationBase } from './base.js';
export { SocialIntegration, socialIntegration } from './social.js';
export { ProductivityIntegration, productivityIntegration } from './productivity.js';
export { MediaIntegration, mediaIntegration } from './media.js';
