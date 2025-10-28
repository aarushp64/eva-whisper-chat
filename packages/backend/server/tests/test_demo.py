import sys
import os

HERE = os.path.dirname(__file__)
SERVER_DIR = os.path.abspath(os.path.join(HERE, '..'))
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from core.agent_factory import AgentFactory
from core.llm.base_llm import Message


def test_demo_simple_echo():
    cfg = None
    agent = AgentFactory.create_agent_no_rag(cfg)
    history = [Message(role='user', content='Hello demo')]
    result = agent.process_query(query='Hello demo', conversation_history=history)

    assert 'stub' in result.get('model', '') or 'stub' in result.get('response', '')
    assert result.get('iterations', 0) >= 1


def test_demo_math_evaluation():
    cfg = None
    agent = AgentFactory.create_agent_no_rag(cfg)
    history = [Message(role='user', content='25 * 4')]
    result = agent.process_query(query='25 * 4', conversation_history=history)

    # Stub's simple math returns 'The result is: 100' or similar
    assert '100' in result.get('response') or 'The result' in result.get('response')
