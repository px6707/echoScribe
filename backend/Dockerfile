# 使用 Python 3.9 基础镜像
FROM python:3.9-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /backend

# 创建模型缓存目录
ENV TRANSFORMERS_CACHE=/root/.cache/huggingface
ENV XDG_CACHE_HOME=/root/.cache

# 复制依赖文件
COPY app/requirements.txt app/

# 安装依赖
RUN pip install --no-cache-dir -r app/requirements.txt

# 复制应用代码
COPY app/ app/

# 创建上传目录并设置权限
RUN mkdir -p app/uploads && chmod 777 app/uploads
VOLUME ["/backend/app/uploads"]

# 设置模型环境变量
ARG WHISPER_MODEL=medium
ENV WHISPER_MODEL=${WHISPER_MODEL}

# 复制本地模型文件
COPY ./models/ /root/.cache/whisper/

# 设置环境变量
ENV PYTHONPATH=/backend
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 8000

# 启动命令将由 docker-compose 提供