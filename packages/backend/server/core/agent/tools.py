"""
Tool definitions and registry for the agent.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from loguru import logger


@dataclass
class ToolParameter:
    """Represents a tool parameter."""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None


class Tool(ABC):
    """Base class for agent tools."""
    
    def __init__(self, name: str, description: str, parameters: List[ToolParameter]):
        self.name = name
        self.description = description
        self.parameters = parameters
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with given parameters.
        
        Returns:
            Dictionary with 'success' boolean and 'result' or 'error'
        """
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary representation."""
        return {
            'name': self.name,
            'description': self.description,
            'parameters': [
                {
                    'name': p.name,
                    'type': p.type,
                    'description': p.description,
                    'required': p.required,
                    'default': p.default
                }
                for p in self.parameters
            ]
        }
    
    def validate_parameters(self, **kwargs) -> tuple[bool, Optional[str]]:
        """
        Validate provided parameters.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        for param in self.parameters:
            if param.required and param.name not in kwargs:
                return False, f"Missing required parameter: {param.name}"
        return True, None


class ToolRegistry:
    """Registry for managing available tools."""
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        logger.info("Tool registry initialized")
    
    def register(self, tool: Tool) -> None:
        """
        Register a tool.
        
        Args:
            tool: Tool instance to register
        """
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def unregister(self, tool_name: str) -> None:
        """
        Unregister a tool.
        
        Args:
            tool_name: Name of tool to unregister
        """
        if tool_name in self.tools:
            del self.tools[tool_name]
            logger.info(f"Unregistered tool: {tool_name}")
    
    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """
        Get a tool by name.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool instance or None if not found
        """
        return self.tools.get(tool_name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools.
        
        Returns:
            List of tool dictionaries
        """
        return [tool.to_dict() for tool in self.tools.values()]
    
    def get_tools_description(self) -> str:
        """
        Get a formatted description of all tools for LLM context.
        
        Returns:
            Formatted string describing all tools
        """
        if not self.tools:
            return "No tools available."
        
        descriptions = ["Available tools:"]
        for tool in self.tools.values():
            params = ", ".join([
                f"{p.name}: {p.type}" + (" (required)" if p.required else " (optional)")
                for p in tool.parameters
            ])
            descriptions.append(f"- {tool.name}({params}): {tool.description}")
        
        return "\n".join(descriptions)


# Built-in Tools

class WebSearchTool(Tool):
    """Tool for searching the web."""
    
    def __init__(self):
        super().__init__(
            name="web_search",
            description="Search the web for information using DuckDuckGo",
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="Search query"
                ),
                ToolParameter(
                    name="max_results",
                    type="integer",
                    description="Maximum number of results to return",
                    required=False,
                    default=5
                )
            ]
        )
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute web search."""
        try:
            from duckduckgo_search import DDGS
            
            query = kwargs.get('query')
            max_results = kwargs.get('max_results', 5)
            
            # Validate parameters
            is_valid, error = self.validate_parameters(**kwargs)
            if not is_valid:
                return {'success': False, 'error': error}
            
            # Perform search
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            
            return {
                'success': True,
                'result': results
            }
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return {'success': False, 'error': str(e)}


class FileReadTool(Tool):
    """Tool for reading file contents."""
    
    def __init__(self):
        super().__init__(
            name="read_file",
            description="Read the contents of a file",
            parameters=[
                ToolParameter(
                    name="file_path",
                    type="string",
                    description="Path to the file to read"
                )
            ]
        )
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute file read."""
        try:
            import os
            
            file_path = kwargs.get('file_path')
            
            # Validate parameters
            is_valid, error = self.validate_parameters(**kwargs)
            if not is_valid:
                return {'success': False, 'error': error}
            
            # Security check - prevent reading sensitive files
            if not os.path.exists(file_path):
                return {'success': False, 'error': 'File not found'}
            
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                'success': True,
                'result': content
            }
        except Exception as e:
            logger.error(f"File read error: {e}")
            return {'success': False, 'error': str(e)}


class CalculatorTool(Tool):
    """Tool for performing calculations."""
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description="Evaluate mathematical expressions safely",
            parameters=[
                ToolParameter(
                    name="expression",
                    type="string",
                    description="Mathematical expression to evaluate (e.g., '2 + 2', 'sqrt(16)')"
                )
            ]
        )
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute calculation."""
        try:
            import ast
            import operator
            import math
            
            expression = kwargs.get('expression')
            
            # Validate parameters
            is_valid, error = self.validate_parameters(**kwargs)
            if not is_valid:
                return {'success': False, 'error': error}
            
            # Safe evaluation with limited operators
            allowed_operators = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
                ast.Pow: operator.pow,
                ast.USub: operator.neg,
            }
            
            allowed_functions = {
                'sqrt': math.sqrt,
                'sin': math.sin,
                'cos': math.cos,
                'tan': math.tan,
                'log': math.log,
                'exp': math.exp,
                'abs': abs,
            }
            
            def eval_expr(node):
                if isinstance(node, ast.Num):
                    return node.n
                elif isinstance(node, ast.BinOp):
                    return allowed_operators[type(node.op)](
                        eval_expr(node.left),
                        eval_expr(node.right)
                    )
                elif isinstance(node, ast.UnaryOp):
                    return allowed_operators[type(node.op)](eval_expr(node.operand))
                elif isinstance(node, ast.Call):
                    func_name = node.func.id
                    if func_name in allowed_functions:
                        args = [eval_expr(arg) for arg in node.args]
                        return allowed_functions[func_name](*args)
                    else:
                        raise ValueError(f"Function {func_name} not allowed")
                else:
                    raise TypeError(f"Unsupported type {type(node)}")
            
            result = eval_expr(ast.parse(expression, mode='eval').body)
            
            return {
                'success': True,
                'result': result
            }
        except Exception as e:
            logger.error(f"Calculator error: {e}")
            return {'success': False, 'error': str(e)}


class CurrentTimeTool(Tool):
    """Tool for getting current time."""
    
    def __init__(self):
        super().__init__(
            name="current_time",
            description="Get the current date and time",
            parameters=[]
        )
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute current time retrieval."""
        try:
            from datetime import datetime
            
            now = datetime.now()
            
            return {
                'success': True,
                'result': {
                    'datetime': now.isoformat(),
                    'formatted': now.strftime('%Y-%m-%d %H:%M:%S'),
                    'timestamp': now.timestamp()
                }
            }
        except Exception as e:
            logger.error(f"Current time error: {e}")
            return {'success': False, 'error': str(e)}
