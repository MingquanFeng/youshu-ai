FROM python:3.13-slim

WORKDIR /app

# 替换为清华 Debian 镜像源，加速 apt 下载
RUN sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libjpeg62-turbo \
    libpng16-16 \
    libtiff6 \
    libwebp7 \
    libopenjp2-7 \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY pyproject.toml .

# 安装核心依赖 + AI 可选依赖
# 使用清华镜像加速，国内服务器构建更快
RUN pip install --no-cache-dir \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    ".[ai]"

# 复制应用代码
COPY . .

# 创建存储目录
RUN mkdir -p /app/storage/uploads

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
