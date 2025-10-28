"""Standalone demo script to show agent outputs without running the full server.

Usage:
    py demo_agent.py "What is 25 * 4?"

This script builds a no-RAG agent that uses the deterministic `OllamaStub` LLM and
prints the agent's response. It's lightweight and doesn't require Ollama or
vector DBs. It still requires Python 3.9+ and the repository files.
"""
import sys
import os

HERE = os.path.dirname(__file__)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from core.config import Config
from core.agent_factory import AgentFactory
from core.llm.base_llm import Message


def main():
    query = "Hello, demo!"
    if len(sys.argv) > 1:
        query = sys.argv[1]

    cfg = Config()
    cfg.llm.provider = 'stub'
    cfg.llm.model_name = 'stub-model'
    cfg.agent.enable_tools = False

    agent = AgentFactory.create_agent_no_rag(cfg)

    history = [Message(role='user', content=query)]
    result = agent.process_query(query=query, conversation_history=history)

    print("--- DEMO QUERY ---")
    print(query)
    print("--- AGENT RESPONSE ---")
    print(result.get('response'))
    print("--- METADATA ---")
    print({
        'iterations': result.get('iterations'),
        'tool_calls': result.get('tool_calls'),
        'model': result.get('model')
    })


if __name__ == '__main__':
    main()
