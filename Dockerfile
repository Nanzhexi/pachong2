# 使用官方的Python基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制当前目录的内容到工作目录
COPY . .

# 安装必要的Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露端口（如果有需要）
# EXPOSE 8000

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 运行Python脚本
CMD ["python", "your_script.py"]
