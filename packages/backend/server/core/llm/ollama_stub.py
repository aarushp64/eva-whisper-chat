"""A minimal, deterministic stub LLM for local development and demo purposes.

This stub implements the same BaseLLM interface used by the real Ollama client
but returns deterministic, safe outputs without any external dependencies.
"""
from typing import List, Optional, AsyncIterator
import asyncio
from .base_llm import BaseLLM, Message, LLMResponse


class OllamaStub(BaseLLM):
    def __init__(self, model_name: str = "stub-model", host: str = "http://localhost:11434", **kwargs):
        super().__init__(model_name, **kwargs)

    def _simple_math(self, text: str) -> Optional[str]:
        # Attempt to find a simple arithmetic expression inside the text
        # Accept expressions like '25 * 4' or '7*6' even when embedded in other words
        import re
        import ast, operator

        # Regex to capture a sequence of numbers and +-*/ operators (simple)
        m = re.search(r"([-+]?\d+(?:\s*[\+\-\*\/]\s*\d+)+)", text)
        if not m:
            return None

        expr = m.group(1)

        ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
        }

        def eval_node(node):
            # Support ast.Constant for newer Python versions
            if hasattr(ast, 'Constant') and isinstance(node, ast.Constant):
                return node.value
            if isinstance(node, ast.Num):
                return node.n
            if isinstance(node, ast.BinOp):
                return ops[type(node.op)](eval_node(node.left), eval_node(node.right))
            if isinstance(node, ast.UnaryOp):
                return ops[type(node.op)](eval_node(node.operand))
            raise ValueError("Unsupported expression")

        try:
            tree = ast.parse(expr, mode='eval')
            result = eval_node(tree.body)
            return str(result)
        except Exception:
            return None

    def generate(self, messages: List[Message], temperature: float = 0.7, max_tokens: Optional[int] = None, **kwargs) -> LLMResponse:
        # Create a structured response by inspecting the last user message
        last = messages[-1].content if messages else ""

        trace = []
        sources = []

        # Initial 'thinking' trace
        trace.append({'phase': 'analysis', 'text': f'Analyzing input: {last}'})

        # If it looks like a math expression, try to evaluate
        math_result = self._simple_math(last)
        if math_result is not None:
            thought = f"Detected arithmetic expression. Computed: {math_result}"
            trace.append({'phase': 'calculation', 'text': thought})
            content = f"The result is: {math_result}"
            sources.append({'type': 'calculator', 'detail': 'stub-evaluator'})
        else:
            # Otherwise, echo with a canned prefix and a simple 'confidence'
            thought = f"Generating echo response for input"
            trace.append({'phase': 'generation', 'text': thought})
            content = f"[stub] I received: {last}"
            sources.append({'type': 'echo', 'detail': 'stub'})

        metadata = {
            'trace': trace,
            'sources': sources,
            'confidence': 0.95
        }

        return LLMResponse(content=content, model=self.model_name, tokens_used=len(content)//4, finish_reason='stub', metadata=metadata)

    async def generate_stream(self, messages: List[Message], temperature: float = 0.7, max_tokens: Optional[int] = None, **kwargs) -> AsyncIterator[str]:
        """Yield the response in multiple chunks to emulate streaming LLM behavior.

        Yields a short 'analysis' chunk, then either a calculation chunk or generation chunk,
        then a final completion chunk.
        """
        # Build the same response content and metadata but stream it
        resp = self.generate(messages, temperature=temperature, max_tokens=max_tokens, **kwargs)

        # Emit 'analysis' chunk
        for t in resp.metadata.get('trace', []):
            yield f"[trace] {t['phase']}: {t['text']}"
            await asyncio.sleep(0)

        # Emit the content in two halves to simulate streaming
        content = resp.content
        mid = len(content) // 2
        yield content[:mid]
        await asyncio.sleep(0)
        yield content[mid:]

    def count_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)

    def get_embeddings(self, text: str):
        # Return a fixed-length pseudo-embedding (deterministic) for tests
        import hashlib
        h = hashlib.sha256(text.encode('utf-8')).digest()
        # convert to floats in range [-1,1]
        vec = [((b / 255.0) * 2 - 1) for b in h[:32]]
        return vec
