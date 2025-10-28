"""
Tool Executor - Handles tool execution and result processing.
"""

from typing import Dict, Any, List, Optional
from loguru import logger
import json
import re

from .tools import ToolRegistry


class ToolExecutor:
    """Executes tools based on agent decisions."""
    
    def __init__(self, tool_registry: ToolRegistry):
        """
        Initialize Tool Executor.
        
        Args:
            tool_registry: Registry of available tools
        """
        self.tool_registry = tool_registry
        logger.info("Tool executor initialized")
    
    def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a specific tool with parameters.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters for the tool
            
        Returns:
            Execution result dictionary
        """
        try:
            tool = self.tool_registry.get_tool(tool_name)
            
            if not tool:
                return {
                    'success': False,
                    'error': f"Tool '{tool_name}' not found"
                }
            
            logger.info(f"Executing tool: {tool_name} with params: {parameters}")
            result = tool.execute(**parameters)
            logger.info(f"Tool execution completed: {tool_name}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def parse_tool_calls_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse tool calls from LLM response text.
        
        Expected format:
        TOOL_CALL: tool_name(param1="value1", param2="value2")
        
        Args:
            text: Text containing tool calls
            
        Returns:
            List of parsed tool calls
        """
        tool_calls = []
        
        # Pattern to match: TOOL_CALL: tool_name(param1="value1", param2=123)
        pattern = r'TOOL_CALL:\s*(\w+)\((.*?)\)'
        matches = re.finditer(pattern, text, re.MULTILINE)
        
        for match in matches:
            tool_name = match.group(1)
            params_str = match.group(2)
            
            try:
                # Parse parameters
                parameters = self._parse_parameters(params_str)
                
                tool_calls.append({
                    'tool_name': tool_name,
                    'parameters': parameters
                })
            except Exception as e:
                logger.error(f"Error parsing tool call parameters: {e}")
                continue
        
        return tool_calls
    
    def _parse_parameters(self, params_str: str) -> Dict[str, Any]:
        """
        Parse parameter string into dictionary.
        
        Args:
            params_str: String like 'param1="value1", param2=123'
            
        Returns:
            Dictionary of parameters
        """
        if not params_str.strip():
            return {}
        
        parameters = {}
        
        # Split by comma, but respect quotes
        param_pattern = r'(\w+)=(".*?"|\'.*?\'|\d+\.?\d*|True|False|None)'
        matches = re.finditer(param_pattern, params_str)
        
        for match in matches:
            key = match.group(1)
            value_str = match.group(2)
            
            # Parse value
            if value_str.startswith('"') or value_str.startswith("'"):
                value = value_str[1:-1]  # Remove quotes
            elif value_str in ('True', 'False'):
                value = value_str == 'True'
            elif value_str == 'None':
                value = None
            elif '.' in value_str:
                value = float(value_str)
            else:
                value = int(value_str)
            
            parameters[key] = value
        
        return parameters
    
    def execute_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute multiple tool calls.
        
        Args:
            tool_calls: List of tool call dictionaries
            
        Returns:
            List of execution results
        """
        results = []
        
        for call in tool_calls:
            result = self.execute_tool(
                tool_name=call['tool_name'],
                parameters=call['parameters']
            )
            
            results.append({
                'tool_name': call['tool_name'],
                'parameters': call['parameters'],
                'result': result
            })
        
        return results
    
    def format_tool_results(self, results: List[Dict[str, Any]]) -> str:
        """
        Format tool execution results for LLM context.
        
        Args:
            results: List of tool execution results
            
        Returns:
            Formatted string
        """
        if not results:
            return "No tool results."
        
        formatted = ["Tool Execution Results:"]
        
        for i, result in enumerate(results, 1):
            tool_name = result['tool_name']
            exec_result = result['result']
            
            if exec_result['success']:
                formatted.append(
                    f"{i}. {tool_name}: SUCCESS\n"
                    f"   Result: {exec_result['result']}"
                )
            else:
                formatted.append(
                    f"{i}. {tool_name}: FAILED\n"
                    f"   Error: {exec_result['error']}"
                )
        
        return "\n".join(formatted)
