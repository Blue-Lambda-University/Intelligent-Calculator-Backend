from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import uuid4
from fastapi import FastAPI, Depends, HTTPException, Header, Query, Request
from app.trace import trace, request_id
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import select, delete, text
from sqlalchemy.orm import Session
from app.config import BUILD_VERSION, COMMIT_SHA, ENVIRONMENT, HISTORY_LIMIT
from app.database import SessionLocal, Calculation, engine, init_db
from app.engine import evaluate, scientific
from app.mcp_server import mcp
from fastmcp import Client

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app=FastAPI(title='Intelligent Calculator API',version='1.0.0',lifespan=lifespan)
# Browser UI normally accesses the same-origin Next.js BFF. Local direct access is explicit.
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:3000'],allow_methods=['GET','POST','DELETE'],allow_headers=['Content-Type','X-Session-ID'])

@app.middleware("http")
async def trace_request(request: Request, call_next):
    incoming = request.headers.get("X-Request-ID", "")
    token = request_id.set(incoming if incoming and len(incoming) <= 64 and incoming.isascii() and incoming.replace("-", "").isalnum() else str(uuid4()))
    try:
        trace("FASTAPI", "Request received", method=request.method, path=request.url.path)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id.get()
        trace("FASTAPI", "Response returned", status=response.status_code)
        return response
    finally:
        request_id.reset(token)

def db_session():
    db=SessionLocal()
    try: yield db
    finally: db.close()

def current_session(x_session_id: str = Header(default='demo',min_length=1,max_length=80)):
    return x_session_id

class BasicRequest(BaseModel):
    expression: str=Field(min_length=1,max_length=256)
class ScientificRequest(BaseModel):
    operation: str
    value: float
    second: float|None=None
    angle_mode: str='degrees'
class AIRequest(BaseModel):
    prompt: str=Field(min_length=1,max_length=500)

def save(db,session,mode,expression,result,original_input=None,explanation=None):
    trace('DATABASE', 'Saving calculation', mode=mode, result=result)
    item=Calculation(session_id=session,mode=mode,expression=expression,result=f'{result:.14g}',original_input=original_input,explanation=explanation)
    db.add(item);db.commit();db.refresh(item)
    trace('DATABASE', 'Calculation committed', mode=mode)
    return {"id":item.id,"mode":mode,"expression":expression,"result":result,"explanation":explanation,"created_at":item.created_at.isoformat()}

def bad(exc):
    trace('FASTAPI', 'Calculation rejected', error_type=type(exc).__name__)
    raise HTTPException(status_code=422,detail={"code":"CALCULATION_ERROR","message":str(exc)}) from exc

@app.post('/api/v1/calculate')
def calculate(payload:BasicRequest,db:Session=Depends(db_session),session:str=Depends(current_session)):
    trace('FASTAPI', 'Basic calculation received', expression_length=len(payload.expression))
    try: result=evaluate(payload.expression)
    except ValueError as exc: bad(exc)
    return save(db,session,'basic',payload.expression,result)

@app.post('/api/v1/scientific')
def calculate_scientific(payload:ScientificRequest,db:Session=Depends(db_session),session:str=Depends(current_session)):
    trace('FASTAPI', 'Scientific calculation received')
    try: result=scientific(payload.operation,payload.value,payload.second,payload.angle_mode)
    except (ValueError, OverflowError) as exc: bad(exc)
    return save(db,session,'scientific',f'{payload.operation}({payload.value}{", "+str(payload.second) if payload.second is not None else ""})',result)

@app.post('/api/v1/ai/calculate')
async def ai_calculate(payload:AIRequest,db:Session=Depends(db_session),session:str=Depends(current_session)):
    trace('FASTAPI', 'AI calculation received; calling MCP', prompt_length=len(payload.prompt))
    # Real in-memory MCP client tool call; deterministic interpretation means CI needs no LLM key.
    try:
        async with Client(mcp) as client:
            tool_result = await client.call_tool('interpret_math_request', {'prompt': payload.prompt})
        if tool_result.is_error:
            raise ValueError('Agent tool rejected the calculation')
        trace('FASTAPI', 'MCP response received')
        data = tool_result.data
        expression, result, explanation = data['expression'], data['result'], data['explanation']
    except (ValueError, KeyError, TypeError) as exc:
        bad(exc)
    return save(db,session,'ai',expression,result,payload.prompt,explanation)

@app.get('/api/v1/history')
def history(limit:int=Query(30,ge=1,le=100),mode:str|None=None,db:Session=Depends(db_session),session:str=Depends(current_session)):
    stmt=select(Calculation).where(Calculation.session_id==session)
    if mode: stmt=stmt.where(Calculation.mode==mode)
    items=db.execute(stmt.order_by(Calculation.created_at.desc(),Calculation.id.desc()).limit(limit)).scalars().all()
    return [{"id":x.id,"mode":x.mode,"expression":x.expression,"original_input":x.original_input,"result":float(x.result),"explanation":x.explanation,"created_at":x.created_at.isoformat()} for x in items]

@app.delete('/api/v1/history')
def clear_history(db:Session=Depends(db_session),session:str=Depends(current_session)):
    count=db.execute(delete(Calculation).where(Calculation.session_id==session)).rowcount
    db.commit();return {"deleted":count}

@app.delete('/api/v1/history/{item_id}')
def delete_history(item_id:str,db:Session=Depends(db_session),session:str=Depends(current_session)):
    count=db.execute(delete(Calculation).where(Calculation.id==item_id,Calculation.session_id==session)).rowcount
    db.commit()
    if not count: raise HTTPException(404,'History item not found')
    return {"deleted":1}

@app.get('/health/live')
def live(): return {"status":"ok"}

@app.get('/health/ready')
def ready():
    try:
        with engine.connect() as conn: conn.execute(text('SELECT 1'))
        return {"status":"ready"}
    except Exception as exc:
        raise HTTPException(status_code=503,detail='Database unavailable') from exc

@app.get('/api/v1/version')
def version():
    return {"version":BUILD_VERSION,"commit":COMMIT_SHA,"environment":ENVIRONMENT,"timestamp":datetime.now(timezone.utc).isoformat()}
