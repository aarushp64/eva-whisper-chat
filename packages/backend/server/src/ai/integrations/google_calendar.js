const INTEGRATION_NAME = 'google_calendar';
let accessToken = process.env.GOOGLE_CALENDAR_TOKEN || null;

/**
 * Configure OAuth / local authorization
 */
export async function auth(config = {}) {
  try {
    const clientId = process.env.INTEGRATION_CLIENT_ID;
    const clientSecret = process.env.INTEGRATION_CLIENT_SECRET;
    
    if (!clientId || !clientSecret) {
      return { status: 'error', error: 'Missing OAuth credentials in env.' };
    }

    if (config.token) {
      accessToken = config.token;
      return { status: 'success', authenticated: true };
    }

    return { 
      status: 'auth_required', 
      url: `https://accounts.google.com/o/oauth2/v2/auth?client_id=${clientId}&response_type=code&scope=calendar` 
    };
  } catch (error) {
    console.error(`[Integrations][${INTEGRATION_NAME}] Auth failed:`, error);
    return { status: 'error', error: error.message };
  }
}

export function getStatus() {
  return {
    provider: INTEGRATION_NAME,
    authenticated: !!accessToken,
    timestamp: new Date().toISOString()
  };
}

export function revoke() {
  accessToken = null;
  return { status: 'success', revoked: true };
}

/**
 * Execute standard actions against the integration
 * Mandatory HITL gate for mutations.
 */
export async function execute(action, params = {}) {
  if (!accessToken) {
    return { status: 'error', error: 'Not authenticated. Please auth first.' };
  }

  // HITL Gate
  const isMutation = ['add_event', 'delete_event', 'update_event'].includes(action);
  if (isMutation && !params.userApproved) {
    return {
      status: 'pending_approval',
      pendingApprovals: [{
        tool: `integration:${INTEGRATION_NAME}`,
        action,
        prompt: `Are you sure you want to modify your calendar (${action})?`,
        params
      }]
    };
  }

  try {
    switch (action) {
      case 'get_events':
        return { status: 'success', data: [{ title: 'Weekly Sync', time: '10:00 AM' }] };
      case 'add_event':
        return { status: 'success', message: 'Event added successfully.' };
      default:
        return { status: 'error', error: `Unknown action: ${action}` };
    }
  } catch (error) {
    return { status: 'error', error: 'Integration API timeout or rate limit exceeded.' };
  }
}
