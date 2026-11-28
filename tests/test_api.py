import os
os.environ['DATABASE_URL']='sqlite:///./test_calculator.db'
from fastapi.testclient import TestClient
from app.main import app
from app.engine import evaluate,scientific,interpret
import pytest

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_math():
    assert evaluate('2+3*4')==14
    assert evaluate('(2+3)*4')==20
    assert scientific('sqrt',144)==12
    assert scientific('sin',30)==pytest.approx(.5)
    assert interpret('15% of 200')[1]==30
    assert interpret('20% discount on $150')[1]==120

@pytest.mark.parametrize('expression',['1/0','__import__("os")','2**1000','1 + name','10//3'])
def test_unsafe_math(expression):
    with pytest.raises(ValueError): evaluate(expression)

def test_api_and_history(client):
    headers={'X-Session-ID':'session-test-a'}
    r=client.post('/api/v1/calculate',json={'expression':'7*8'},headers=headers)
    assert r.status_code==200 and r.json()['result']==56
    assert len(client.get('/api/v1/history',headers=headers).json())>=1
    assert client.get('/api/v1/history',headers={'X-Session-ID':'other-session'}).json()==[]
    assert client.delete('/api/v1/history',headers=headers).status_code==200
    assert client.get('/api/v1/history',headers=headers).json()==[]

def test_errors(client):
    assert client.post('/api/v1/calculate',json={'expression':'1/0'}).status_code==422
    assert client.post('/api/v1/scientific',json={'operation':'sqrt','value':-4}).status_code==422
    assert client.post('/api/v1/ai/calculate',json={'prompt':'who won the game?'}).status_code==422

def test_health(client):
    assert client.get('/health/live').status_code==200
    assert client.get('/health/ready').status_code==200
    assert 'version' in client.get('/api/v1/version').json()
