from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()

class Calculation(Base):
    __tablename__ = "calculations"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    session_id = Column(String(80), nullable=False, index=True)
    mode = Column(String(20), nullable=False)
    expression = Column(Text, nullable=False)
    original_input = Column(Text, nullable=True)
    result = Column(String(120), nullable=False)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

def init_db():
    Base.metadata.create_all(bind=engine)
