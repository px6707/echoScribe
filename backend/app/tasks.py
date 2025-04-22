import dramatiq
from dramatiq.brokers.redis import RedisBroker
from .models import TranscriptionTask, SessionLocal, get_shanghai_now
from datetime import datetime
import whisper
import torch
import os
import logging
import gc
import psutil
from typing import Optional
from pathlib import Path
from .config import REDIS_HOST, REDIS_PORT, REDIS_DB, UPLOAD_DIR, WHISPER_MODEL

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 设置 Redis broker
redis_broker = RedisBroker(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
dramatiq.set_broker(redis_broker)

# 根据环境选择默认模型
if WHISPER_MODEL:
    MODEL_NAME = WHISPER_MODEL
    logger.info(f'使用用户指定模型: {MODEL_NAME}')
else:
    if torch.cuda.is_available():
        MODEL_NAME = "large-v2"
        logger.info(f'GPU环境，使用默认模型: {MODEL_NAME}')
    else:
        MODEL_NAME = "medium"
        logger.info(f'CPU环境，使用默认模型: {MODEL_NAME}')

def get_session():
    """为每个任务创建独立的数据库会话"""
    return SessionLocal()

def update_task_status(task_id: str, status: str, error: str = None, result: str = None):
    """更新任务状态"""
    session = get_session()
    try:
        # 只更新需要的字段
        update_dict = {"status": status}
        if error:
            update_dict["error"] = error
        if result:
            update_dict["result"] = result
            update_dict["completed_at"] = get_shanghai_now()
        
        # 使用原生UPDATE语句
        session.query(TranscriptionTask).filter_by(id=task_id).update(
            update_dict,
            synchronize_session=False
        )
        session.commit()
    except Exception as e:
        logger.error(f"更新任务状态失败: {str(e)}")
        session.rollback()
    finally:
        session.close()

def clean_memory():
    """清理系统内存和GPU内存"""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    gc.collect()
    
    # 强制回收内存
    process = psutil.Process(os.getpid())
    process.memory_info()

@dramatiq.actor(
    max_retries=3,
    min_backoff=10000,  # 10秒
    max_backoff=600000,  # 10分钟
    time_limit=3600000,  # 1小时
    queue_name="transcribe"
)
def transcribe_audio_task(task_id: str, file_name: str):
    """音频转录任务"""
    logger.info(f"开始处理任务 {task_id}")
    session = get_session()
    model = None

    try:
        # 1. 检查文件
        abs_file_path = UPLOAD_DIR / file_name
        logger.info(f"检查文件: {abs_file_path}")
        
        if not abs_file_path.is_file():
            raise FileNotFoundError(f"音频文件不存在: {abs_file_path}")

        # 2. 验证任务存在并更新状态
        task = session.query(TranscriptionTask).get(task_id)
        if not task:
            raise ValueError(f"任务不存在: {task_id}")
        update_task_status(task_id, "processing")

        # 3. 加载模型并转录
        model = whisper.load_model(MODEL_NAME)
        result = model.transcribe(
            str(abs_file_path),
            language='zh',
            initial_prompt="以下是普通话的转录：",
            temperature=0.0,
            best_of=1,
            fp16=False,
            condition_on_previous_text=True,
        )

        # 4. 更新结果
        update_task_status(task_id, "completed", result=result["text"])
        logger.info("转录完成")

    except Exception as e:
        logger.error(f"转录失败: {str(e)}", exc_info=True)
        update_task_status(task_id, "failed", error=str(e))
        raise

    finally:
        session.close()
        # 删除临时文件
        try:
            if abs_file_path.exists():
                abs_file_path.unlink()
                logger.info(f"已删除音频文件: {abs_file_path}")
        except Exception as e:
            logger.error(f"删除文件失败: {str(e)}")
        clean_memory()