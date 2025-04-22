# EchoScribe 音视频转录服务

基于 OpenAI Whisper 的音视频转录服务，支持中文音视频文件的自动转录。

## 功能特点

- 支持多种音视频格式（MP3, WAV, M4A, OGG, MP4, MPEG, MPGA, WEBM）
- 支持批量上传和处理
- 实时显示转录进度
- 支持导出转录结果为 Excel
- 支持删除历史记录
- 使用 Docker 容器化部署
- 支持后台异步转录处理
- 跨平台兼容（Windows/Mac/Linux）

## 技术栈

### 后端
- FastAPI：Web 框架
- Dramatiq + Redis：任务队列
- SQLAlchemy：ORM
- OpenAI Whisper：音视频转录
- Python 3.9+

### 前端
- Vue 3：前端框架
- Element Plus：UI 组件库
- Vite：构建工具

## 快速开始

### Windows 平台

1. 克隆项目：
```bash
git clone https://github.com/yourusername/echoscribe.git
cd echoscribe
```

2. 使用批处理脚本快速设置：
```bash
# 一键下载模型并构建 Docker 镜像
setup.bat

# 启动服务
docker-compose up
```

### Mac/Linux 平台

1. 克隆项目：
```bash
git clone https://github.com/yourusername/echoscribe.git
cd echoscribe
```

2. 使用 Makefile 快速设置：
```bash
# 一键下载模型并构建 Docker 镜像
make setup

# 或者分步执行：
make download-model  # 仅下载模型
make build          # 仅构建 Docker 镜像

# 启动服务
docker-compose up
```

### 访问服务

- 前端界面：http://localhost
- API 文档：http://localhost:8000/docs

### 本地开发

1. 后端设置：
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r app/requirements.txt
```

2. 启动服务：
```bash
# 终端 1：启动 Redis（如果没有安装，请先安装 Redis）
redis-server

# 终端 2：启动后端 API 服务
python run.py

# 终端 3：启动 Dramatiq Worker（处理转录任务）
python -m dramatiq app.tasks -p 2 -t 1
```

3. 前端设置：
```bash
cd frontend/echoscribe-frontend
npm install
npm run dev
```

## 环境变量

### 后端环境变量
- `REDIS_HOST`：Redis 服务器地址（默认：localhost）
- `REDIS_PORT`：Redis 端口（默认：6379）
- `REDIS_DB`：Redis 数据库（默认：0）
- `WHISPER_MODEL`：Whisper 模型大小（默认：medium）

## 后台任务配置

### Worker 配置
- `-p`：worker 进程数（建议：CPU 核心数）
- `-t`：每个进程的线程数（默认：1）
- `--queue`：指定队列名（默认：default）

### 任务重试机制
- 最大重试次数：3次
- 最小重试间隔：10秒
- 最大重试间隔：10分钟
- 任务超时时间：1小时

### 任务状态
- `pending`：等待处理
- `processing`：处理中
- `completed`：处理完成
- `failed`：处理失败

### 监控和维护
1. 查看任务状态：
   - 通过前端界面查看
   - 访问 API：`GET /tasks`

2. 清理任务：
   - 通过前端界面删除
   - 调用 API：`DELETE /tasks`

3. 导出结果：
   - 通过前端界面导出
   - 调用 API：`POST /export`

## API 接口

### 主要接口
- `POST /upload`：上传音视频文件
- `GET /tasks`：获取任务列表
- `DELETE /tasks`：删除任务
- `POST /export`：导出转录结果

## 目录结构

```
echoscribe/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI 应用
│   │   ├── models.py        # 数据模型
│   │   ├── tasks.py         # 异步任务
│   │   └── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── Makefile
└── setup.bat
```

## 注意事项

1. 文件大小限制：单个文件最大 500MB
2. 支持的音视频格式：MP3, WAV, M4A, OGG, MP4, MPEG, MPGA, WEBM
3. 转录任务可能需要较长时间，取决于文件大小和服务器性能
4. 建议使用 Docker 部署以确保环境一致性

## 许可证

MIT License