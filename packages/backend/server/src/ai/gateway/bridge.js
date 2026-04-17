class GatewayBridge {
  constructor() {
    this.pythonServiceUrl = process.env.PYTHON_SERVICE_URL || 'http://localhost:5000/api/v1';
    this.timeout = parseInt(process.env.GATEWAY_TIMEOUT, 10) || 15000;
  }

  async checkHealth() {
    try {
      const response = await fetch(`${this.pythonServiceUrl}/health`, { signal: AbortSignal.timeout(3000) });
      return response.ok ? 'connected' : 'degraded';
    } catch {
      return 'disconnected';
    }
  }

  async dispatch(taskType, payload) {
    try {
      const response = await fetch(`${this.pythonServiceUrl}/dispatch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_type: taskType,
          payload,
          timestamp: Date.now()
        }),
        signal: AbortSignal.timeout(this.timeout)
      });

      if (!response.ok) {
        throw new Error(`Python Gateway responded with HTTP ${response.status}`);
      }

      const raw = await response.json();
      return raw.data;
    } catch (error) {
      console.error('[Gateway] Python bridge execution failed:', error.message);
      return { _gateway_fallback: true, error: error.message };
    }
  }
}

export const gateway = new GatewayBridge();
