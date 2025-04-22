@echo off
echo === EchoScribe Setup Script for Windows ===

:: 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed! Please install Python 3.10 or later.
    exit /b 1
)

:: 检查 Docker 是否安装
docker --version >nul 2>&1
if errorlevel 1 (
    echo Docker is not installed! Please install Docker Desktop for Windows.
    exit /b 1
)

:: 创建模型目录
echo Creating model directory...
if not exist "backend\models" mkdir "backend\models"

:: 下载模型
echo Downloading Whisper model...
python -c "import whisper; whisper.load_model('medium')"

:: 复制模型文件
echo Copying model files...
xcopy /E /I /Y "%USERPROFILE%\.cache\whisper\*" "backend\models\"

:: 构建 Docker 镜像
echo Building Docker images...
docker-compose build

echo Setup completed successfully!
echo You can now run 'docker-compose up' to start EchoScribe.