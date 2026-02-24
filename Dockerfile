# ⚔️ 三省六部 · Demo Dashboard
# docker run -p 7891:7891 cft0808/sansheng-demo
# Then open: http://localhost:7891

FROM python:3.11-slim

WORKDIR /app

# 复制看板核心文件
COPY dashboard/ ./dashboard/
COPY scripts/ ./scripts/

# 注入演示数据（data目录由demo_data提供）
COPY docker/demo_data/ ./data/

EXPOSE 7891

CMD ["python3", "dashboard/server.py", "--host", "0.0.0.0", "--port", "7891"]
