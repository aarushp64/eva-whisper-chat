"""
Agent Framework

Provides tool execution, reasoning, and action capabilities for Eva.
The agent can:
- Execute tools (web search, file operations, code execution)
- Reason about tasks and break them down
- Learn from interactions
- Make decisions autonomously
"""

from .agent import Agent
from .tools import Tool, ToolRegistry
from .executor import ToolExecutor

__all__ = ['Agent', 'Tool', 'ToolRegistry', 'ToolExecutor']
