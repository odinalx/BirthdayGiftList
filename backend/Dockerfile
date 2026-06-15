FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN groupadd -r appgroup && useradd -r -g appgroup -m appuser

WORKDIR /app

COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev || uv sync --no-dev

COPY . .

RUN chown -R appuser:appgroup /app \
    && mkdir -p /home/appuser/.cache && chown -R appuser:appgroup /home/appuser

USER appuser

EXPOSE 8000

CMD ["sh", "entrypoint.sh", "uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
