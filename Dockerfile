FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen

COPY . .

EXPOSE 8501

CMD ["uv", "run", "bash", "-c", "PYTHONPATH=/app streamlit run app/main.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true"]