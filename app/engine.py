"""Allowlisted math parser: no eval/exec or arbitrary function calls."""
from app.trace import trace
import ast
import math
import operator
import re
from decimal import Decimal, InvalidOperation

MAX_LENGTH = 256
MAX_ABS = 1e100
BINARY = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
          ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod}
UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}

def checked(value):
    if isinstance(value, complex) or not isinstance(value, (int, float)):
        raise ValueError("Result must be a real number")
    if not math.isfinite(value) or abs(value) > MAX_ABS:
        raise ValueError("Result exceeds supported numeric range")
    return value

def evaluate(expression: str) -> float:
    trace('ENGINE', 'Evaluating expression', expression=expression)
    if not expression or len(expression) > MAX_LENGTH:
        raise ValueError("Expression length must be between 1 and 256")
    try:
        tree = ast.parse(expression.replace('×','*').replace('÷','/').replace('^','**'), mode='eval')
    except SyntaxError as exc:
        raise ValueError("Invalid mathematical expression") from exc
    def visit(node, depth=0):
        if depth > 24:
            raise ValueError("Expression too deeply nested")
        if isinstance(node, ast.Constant) and type(node.value) in (float,int):
            return checked(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in BINARY:
            a,b=visit(node.left, depth+1),visit(node.right, depth+1)
            if isinstance(node.op, ast.Pow) and (abs(b)>100 or abs(a)>1e6):
                raise ValueError("Exponent exceeds safe limits")
            if isinstance(node.op,(ast.Div,ast.Mod)) and b==0:
                raise ValueError("Division by zero")
            try:
                value = checked(BINARY[type(node.op)](a,b))
                trace('ENGINE', 'Binary operation', operator=type(node.op).__name__, left=a, right=b, result=value)
                return value
            except (OverflowError,ZeroDivisionError) as exc: raise ValueError("Invalid numeric operation") from exc
        if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY:
            return checked(UNARY[type(node.op)](visit(node.operand,depth+1)))
        raise ValueError("Unsupported expression")
    result = float(visit(tree.body))
    trace('ENGINE', 'Arithmetic result', result=result)
    return result

def scientific(operation: str, value: float, second: float | None = None, angle_mode: str='degrees') -> float:
    trace('ENGINE', 'Scientific calculation started', operation=operation, value=value, second=second, angle_mode=angle_mode)
    checked(value)
    if angle_mode not in ('degrees','radians'):
        raise ValueError("Invalid angle mode")
    if operation in ('sin','cos','tan'):
        x=math.radians(value) if angle_mode=='degrees' else value
        if operation=='tan' and abs(math.cos(x))<1e-12:
            raise ValueError("Tangent undefined at this angle")
        return checked(getattr(math,operation)(x))
    if operation=='sqrt':
        if value<0: raise ValueError("Square root requires nonnegative input")
        return math.sqrt(value)
    if operation in ('log10','ln'):
        if value<=0: raise ValueError("Logarithm requires positive input")
        return math.log10(value) if operation=='log10' else math.log(value)
    if operation=='factorial':
        if not value.is_integer() or value<0 or value>170:
            raise ValueError("Factorial requires integer from 0 to 170")
        return float(math.factorial(int(value)))
    if operation=='power':
        if second is None: raise ValueError("Power requires a second number")
        return evaluate(f'({value})**({second})')
    if operation=='percent':
        if second is None: raise ValueError("Percent requires a second number")
        return checked(value*second/100)
    raise ValueError("Unsupported scientific operation")

PATTERNS = [
 (r'what is ([-+]?\d+(?:\.\d+)?)\s*% of ([-+]?\d+(?:\.\d+)?)\??', 'percent'),
 (r'([-+]?\d+(?:\.\d+)?)\s*% of ([-+]?\d+(?:\.\d+)?)', 'percent'),
 (r'(?:divide|split)\s+([-+]?\d+(?:\.\d+)?)\s+(?:equally )?(?:between|among|by)\s+([-+]?\d+(?:\.\d+)?)', 'divide'),
 (r'(?:square root of|sqrt)\s+([-+]?\d+(?:\.\d+)?)', 'sqrt'),
 (r'(?:what is |calculate )?([-+]?\d+(?:\.\d+)?)\s*([+*/x×-])\s*([-+]?\d+(?:\.\d+)?)', 'arithmetic'),
 (r'(?:calculate )?([-+]?\d+(?:\.\d+)?)\s*% discount on \$?([-+]?\d+(?:\.\d+)?)', 'discount'),
]

def interpret(text: str) -> tuple[str,float,str]:
    """Offline deterministic natural-language adapter for repeatable CI tests."""
    if len(text)>500 or not text.strip(): raise ValueError("Prompt must be 1 to 500 characters")
    prompt=text.strip().lower().replace(',','')
    # Discount must be evaluated before percentage patterns.
    patterns=[PATTERNS[-1]] + PATTERNS[:-1]
    for pattern,kind in patterns:
        match=re.fullmatch(pattern,prompt)
        if not match: continue
        vals=match.groups()
        trace('ENGINE', 'Natural language rule matched', rule=kind, operands=vals)
        if kind=='percent':
            a,b=map(float,vals); result=scientific('percent',a,b)
            return f'{b} * {a} / 100',result,f'{a}% of {b} is {result:g}.'
        if kind=='discount':
            a,b=map(float,vals);result=checked(b-scientific('percent',a,b))
            return f'{b} - ({b} * {a} / 100)',result,f'After a {a}% discount, the price is {result:g}.'
        if kind=='divide':
            a,b=map(float,vals);result=evaluate(f'{a}/{b}')
            return f'{a}/{b}',result,f'Split {a:g} into {b:g} equal parts: {result:g} each.'
        if kind=='sqrt':
            a=float(vals[0]); result=scientific('sqrt',a)
            return f'sqrt({a})',result,f'The square root of {a:g} is {result:g}.'
        if kind=='arithmetic':
            a,op,b=vals; op='*' if op in ('x','×') else op
            exp=f'{a}{op}{b}'; result=evaluate(exp)
            return exp,result,f'{a} {op} {b} = {result:g}.'
    raise ValueError("I cannot interpret that request. Try '15% of 200' or 'divide 850 among 5'.")
