import sys
import os

HERE = os.path.dirname(__file__)
SERVER_DIR = os.path.abspath(os.path.join(HERE, '..'))
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from core.agent_factory import AgentFactory
from core.llm.base_llm import Message


def test_demo_metadata_present():
    agent = AgentFactory.create_agent_no_rag()
    history = [Message(role='user', content='What is 7 * 6')]
    result = agent.process_query(query='What is 7 * 6', conversation_history=history)

    assert 'llm_metadata' in result
    meta = result['llm_metadata']
    assert 'trace' in meta
    assert isinstance(meta['trace'], list)
    assert any('calculation' in t.get('phase','') or 'calculation' in t.get('text','') for t in meta['trace'])
 