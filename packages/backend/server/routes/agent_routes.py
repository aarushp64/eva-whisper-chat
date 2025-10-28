"""
API routes for the AI Agent.
"""

from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from loguru import logger
import json
import asyncio

from core.agent_factory import get_agent
import requests
from core.llm.base_llm import Message

agent_bp = Blueprint('agent', __name__)


@agent_bp.route('/query', methods=['POST'])
@jwt_required(optional=True)
def agent_query():
    """
    Process a query through the agent.
    
    Request body:
    {
        "query": "What is the weather like?",
        "conversation_history": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"}
        ]
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({'error': 'Missing query parameter'}), 400
        
        query = data['query']
        conversation_history = data.get('conversation_history', [])
        
        # Convert conversation history to Message objects
        history_messages = [
            Message(role=msg['role'], content=msg['content'])
            for msg in conversation_history
        ]
        
        # Get user ID if authenticated
        user_id = None
        try:
            user_id = get_jwt_identity()
        except:
            pass
        
        # Get agent and process query (create agent safely)
        try:
            agent = get_agent()
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            return jsonify({'error': 'Agent not available', 'details': str(e)}), 503

        if agent is None:
            return jsonify({'error': 'Agent not available'}), 503

        result = agent.process_query(
            query=query,
            conversation_history=history_messages,
            user_id=user_id
        )
        
        return jsonify({
            'success': True,
            'response': result['response'],
            'tool_calls': result.get('tool_calls', []),
            'iterations': result.get('iterations', 1),
            'context_used': len(result.get('context_used', [])),
                'model': result.get('model'),
                'llm_metadata': result.get('llm_metadata')
        })
        
    except Exception as e:
        logger.error(f"Error in agent query: {e}")
        return jsonify({'error': str(e)}), 500


@agent_bp.route('/stats', methods=['GET'])
def agent_stats():
    """Get agent statistics."""
    try:
        try:
            agent = get_agent()
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            return jsonify({'error': 'Agent not available', 'details': str(e)}), 503

        if agent is None:
            return jsonify({'error': 'Agent not available'}), 503

        stats = agent.get_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting agent stats: {e}")
        return jsonify({'error': str(e)}), 500


@agent_bp.route('/tools', methods=['GET'])
def list_tools():
    """List available tools."""
    try:
        try:
            agent = get_agent()
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            return jsonify({'error': 'Agent not available', 'details': str(e)}), 503

        if agent is None:
            return jsonify({'error': 'Agent not available'}), 503

        tools = agent.tool_registry.list_tools()
        
        return jsonify({
            'success': True,
            'tools': tools
        })
        
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        return jsonify({'error': str(e)}), 500


@agent_bp.route('/demo', methods=['POST'])
def agent_demo():
    """Return a deterministic demo response using the stub LLM (no external services).

    Request body:
    { "query": "What's 2+2?" }
    """
    try:
        data = request.get_json() or {}
        query = data.get('query', 'Hello from demo')

        # Build a minimal config that uses the stub provider
        from core.config import Config
        from core.agent_factory import AgentFactory
        from core.llm.base_llm import Message

        cfg = Config()
        cfg.llm.provider = 'stub'
        cfg.llm.model_name = 'stub-model'
        cfg.agent.enable_tools = False

        agent = AgentFactory.create_agent_no_rag(cfg)
        # call agent with simple Message history
        history = [Message(role='user', content=query)]
        result = agent.process_query(query=query, conversation_history=history)

        return jsonify({'success': True, 'response': result.get('response')})
    except Exception as e:
        logger.error(f"Error in agent demo: {e}")
        return jsonify({'error': str(e)}), 500
