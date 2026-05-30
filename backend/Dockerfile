FROM python:3.14.5-slim-trixie

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ARG USERNAME=zeitzeit

RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  libffi-dev \
  && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 $USERNAME \
  && useradd --uid 1000 --gid 1000 -m $USERNAME

WORKDIR /app

RUN chown $USERNAME:$USERNAME /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"

USER $USERNAME

RUN --mount=type=cache,target=/home/$USERNAME/.cache/uv,uid=1000 \
  --mount=type=bind,source=uv.lock,target=uv.lock \
  --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
  uv sync --frozen --no-install-project

ADD --chown=$USERNAME:$USERNAME . /app

RUN --mount=type=cache,target=/home/$USERNAME/.cache/uv,uid=1000 \
  uv sync --frozen

ENTRYPOINT []

EXPOSE 8000

CMD ["fastapi", "dev", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
