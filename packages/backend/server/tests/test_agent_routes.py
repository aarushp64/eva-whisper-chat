import os
import sys
import json

# Ensure server package directory is on path so imports like 'core' and 'routes' work
HERE = os.path.dirname(__file__)
SERVER_DIR = os.path.abspath(os.path.join(HERE))
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

import pytest

# Import the Flask app instance
from app import app as flask_app
import core.agent_factory as agent_factory


class StubAgent:
    def process_query(self, query, conversation_history=None, user_id=None):
        return {
            'response': 'stubbed response',
            'tool_calls': [],
            'iterations': 1,
            'context_used': [],
            'model': 'stub-model'
        }

    def get_stats(self):
        return {'uptime': 0}

    @property
    def tool_registry(self):
        class TR:
            def list_tools(self):
                return []
        return TR()


def test_agent_query_stub(monkeypatch):
    # Replace the real get_agent with a stub to avoid external calls
    monkeypatch.setattr(agent_factory, 'get_agent', lambda force_recreate=False: StubAgent())

    client = flask_app.test_client()
    resp = client.post('/api/agent/query', json={'query': 'what is 2+2?'})

    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data['response'] == 'stubbed response'


def test_health_endpoint():
    client = flask_app.test_client()
    resp = client.get('/api/health')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'service' in data
    assert data['service'] == 'eva-backend'
