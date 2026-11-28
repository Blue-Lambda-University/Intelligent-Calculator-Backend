"""FastMCP tools reusable by MCP clients; REST calculator shares the engine."""
from fastmcp import FastMCP
from app.trace import trace
from app.engine import evaluate, scientific, interpret
mcp = FastMCP("Intelligent Calculator", instructions="Use calculator tools for mathematical answers; do not calculate in the language model.")

@mcp.tool()
def calculate_expression(expression: str) -> dict:
    """Safely evaluate arithmetic with + - * / % and parentheses."""
    return {"expression": expression, "result": evaluate(expression)}

@mcp.tool()
def scientific_calculation(operation: str, value: float, second: float | None = None, angle_mode: str = "degrees") -> dict:
    """Calculate sqrt, power, percent, factorial, sin/cos/tan, log10 or ln."""
    return {"operation": operation, "result": scientific(operation,value,second,angle_mode)}

@mcp.tool()
def interpret_math_request(prompt: str) -> dict:
    """Interpret a small set of natural language arithmetic requests deterministically."""
    trace('MCP', 'interpret_math_request invoked', prompt_length=len(prompt))
    expression,result,explanation=interpret(prompt)
    trace('MCP', 'Tool result ready', result=result)
    return {"expression":expression,"result":result,"explanation":explanation}

if __name__ == '__main__':
    mcp.run(transport='stdio')
