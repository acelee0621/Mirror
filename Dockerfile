# -------------- 构建阶段 (Builder Stage) --------------
# 使用一个轻量的 Python 镜像作为基础
FROM python:3.13.5-slim AS builder

# 设置工作目录
WORKDIR /app

# 将 uv 从官方镜像中复制到我们的构建环境中，这是一个高效的技巧
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# 仅复制依赖定义文件，以利用 Docker 的层缓存机制
# 只有当这些文件变化时，下面的依赖安装步骤才会重新运行
COPY pyproject.toml uv.lock ./

# 使用 uv 创建虚拟环境并安装所有依赖
# --system-site-packages 确保虚拟环境能访问到基础镜像的包
RUN uv sync --frozen --no-cache

# 复制项目的全部代码到工作目录
COPY . .

# -------------- 运行阶段 (Runner Stage) --------------
# 使用同一个轻量的 Python 镜像
FROM python:3.13.5-slim

# 设置工作目录
WORKDIR /app

# 创建一个没有特权的普通用户 `appuser` 来运行应用，增强安全性
RUN useradd --create-home appuser
# 将工作目录的所有权交给 appuser
RUN chown -R appuser:appuser /app

# 从构建阶段复制已经包含代码和虚拟环境的整个 /app 目录
# 这样做非常高效，避免了在运行阶段再次安装依赖
COPY --from=builder --chown=appuser:appuser /app /app

# 切换到非特权用户
USER appuser

# 将虚拟环境的 bin 目录添加到 PATH 环境变量中
# 这样我们就可以直接运行 uvicorn, streamlit, taskiq 等命令
ENV PATH="/app/.venv/bin:$PATH"

# 暴露 FastAPI 和 Streamlit 将要使用的端口
EXPOSE 8000
EXPOSE 8501

# 默认启动命令（虽然在 docker-compose 中会被覆盖，但这是一个好习惯）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
