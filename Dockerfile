FROM python:3.10-slim-bookworm AS base

FROM base AS builder

COPY --from=ghcr.io/astral-sh/uv:0.7.13 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

WORKDIR /motiva

COPY uv.lock pyproject.toml /motiva/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

COPY . /motiva

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

FROM base
COPY --from=builder /motiva /motiva
ENV PATH="/motiva/.venv/bin:$PATH"
EXPOSE 8000
CMD ["chainlit", "run", "motiva/chainlit_app.py", "--host", "0.0.0.0", "--port", "8000"]