import sys
import os

HERE = os.path.dirname(__file__)
SERVER_DIR = os.path.abspath(os.path.join(HERE, '..'))
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from core.agent_factory import AgentFactory
from core.llm.base_llm import Message


def test_demo_echo_fast():
    agent = AgentFactory.create_agent_no_rag()
    history = [Message(role='user', content='fast demo')]
    result = agent.process_query(query='fast demo', conversation_history=history)
    assert result is not None
    assert result.get('iterations', 0) >= 1


def test_demo_math_fast():
    agent = AgentFactory.create_agent_no_rag()
    history = [Message(role='user', content='6 * 7')]
    result = agent.process_query(query='6 * 7', conversation_history=history)
    assert '42' in result.get('response') or 'result' in result.get('response')
