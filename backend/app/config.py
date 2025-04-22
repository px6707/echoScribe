import os
from pathlib import Path
from dotenv import load_dotenv

# 只在非 Docker 环境下加载 .env 文件
if not os.getenv("DOCKER_ENV"):
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print("已加载本地环境变量配置")

# Redis 配置
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Whisper 配置
WHISPER_MODEL = os.getenv("WHISPER_MODEL")

# 文件路径配置
WORK_DIR = Path(__file__).parent
UPLOAD_DIR = WORK_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)