import whisper
import torch
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def preload_models():
    # 获取用户指定的模型名称
    user_model = os.getenv("WHISPER_MODEL")

    # 根据环境选择默认模型
    if user_model:
        MODEL_NAME = user_model
        logger.info(f'使用用户指定模型: {MODEL_NAME}')
    else:
        if torch.cuda.is_available():
            MODEL_NAME = "large-v2"
            logger.info(f'GPU环境，使用默认模型: {MODEL_NAME}')
        else:
            MODEL_NAME = "medium"
            logger.info(f'CPU环境，使用默认模型: {MODEL_NAME}')
        
    logger.info(f'开始加载模型: {MODEL_NAME}')
    whisper.load_model(MODEL_NAME)
    logger.info('模型加载完成')

if __name__ == "__main__":
    preload_models()