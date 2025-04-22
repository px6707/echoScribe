from sqlalchemy import Column, String, DateTime, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import pytz
import os
from pathlib import Path

# 创建数据目录
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

Base = declarative_base()

def get_shanghai_now():
    """获取当前上海时间"""
    shanghai_tz = pytz.timezone('Asia/Shanghai')
    return datetime.now(shanghai_tz)

class TranscriptionTask(Base):
    __tablename__ = "transcription_tasks"

    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    status = Column(String, nullable=False)  # pending, processing, completed, failed
    created_at = Column(DateTime(timezone=True), default=get_shanghai_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)

# 数据库连接
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/whisper.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建表
Base.metadata.create_all(bind=engine)