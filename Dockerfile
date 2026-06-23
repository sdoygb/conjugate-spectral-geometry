FROM python:3.11-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONHOME="" \
    PYTHONPATH="" \
    HF_ENDPOINT=https://hf-mirror.com \
    SENTENCE_TRANSFORMERS_HOME=/app/models_cache \
    OPENAI_API_BASE_URLS=http://localhost:5000/v1 \
    OPENAI_API_KEYS=not-needed

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git \
    && rm -rf /var/lib/apt/lists/*

# 先复制 requirements.txt（利用 Docker 缓存层）
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装 Open WebUI
RUN pip install --no-cache-dir open-webui \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制应用代码
COPY app/ .

# 创建数据目录
RUN mkdir -p /app/logs /app/models_cache /app/data/chroma_db /app/data/articles

# 暴露端口
# 5000: Geometry AI Server
# 8080: Open WebUI
EXPOSE 5000 8080

# 启动脚本
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
