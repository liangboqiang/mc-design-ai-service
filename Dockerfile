# 使用官方 Python 3.12 镜像作为基础镜像
FROM python:3.12-slim-bookworm AS base

# 安装必要的网络工具
RUN sed -i 's@deb.debian.org@mirrors.huaweicloud.com@g' /etc/apt/sources.list.d/debian.sources
RUN apt-get update && apt-get install -y \
    iputils-ping \
    telnet \
    curl \      
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 设置环境变量
# 防止 Python 生成 .pyc 文件
ENV PYTHONDONTWRITEBYTECODE=1
# 确保 Python 输出直接打印到控制台，而不是缓冲
ENV PYTHONUNBUFFERED=1

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
# 使用阿里云镜像源加速安装
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.huaweicloud.com/repository/pypi/simple

# 复制项目代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动应用
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
