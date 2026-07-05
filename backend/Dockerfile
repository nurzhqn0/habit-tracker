FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv

COPY --from=ghcr.io/astral-sh/uv:0.7 /uv /usr/local/bin/uv

WORKDIR /srv/app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app

RUN addgroup --system habitflow && adduser --system --ingroup habitflow habitflow \
    && mkdir -p /srv/app/data && chown -R habitflow:habitflow /srv/app/data
USER habitflow

ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 8000
# API by default; the bot service overrides the command.
# --proxy-headers: trust X-Forwarded-For from nginx so rate limiting sees real client IPs.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'"]
