.PHONY: download-model build

# 下载模型并复制到正确位置
download-model:
	rm -rf backend/models
	mkdir -p backend/models
	python3 -c "import whisper; whisper.load_model('medium')"
	cp -r ~/.cache/whisper/* backend/models/

# 构建 Docker 镜像
build: download-model
	docker-compose build

# 一键下载模型并构建
setup: download-model build

### 使用： make setup