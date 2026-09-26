FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /usr/local/bin/uv

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH" \
    DATA_DIR=/data

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev

COPY . .
RUN SECRET_KEY=collectstatic python manage.py collectstatic --noinput

RUN useradd --uid 1000 --no-create-home app && mkdir -p /data && chown app:app /data
USER app

EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --noinput && exec gunicorn server.wsgi"]
