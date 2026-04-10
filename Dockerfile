FROM python:3.12-slim

LABEL maintainer="SkillForge Contributors"
LABEL description="SkillForge — Stateless AI skill runtime"

# System deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY pyproject.toml .
COPY README.md .
COPY skillforge/ skillforge/
COPY cli/ cli/
COPY skills/ skills/
COPY pipelines/ pipelines/
COPY tests/ tests/
COPY STANDARD.md .
COPY AGENTS.md .

RUN pip install --no-cache-dir -e ".[dev]"

# Expose API port
EXPOSE 9147

# Health check (stdlib only — no httpx dependency required)
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9147/health')"

# Default: start the web panel + API
CMD ["uvicorn", "skillforge.api.app:app", "--host", "0.0.0.0", "--port", "9147"]

