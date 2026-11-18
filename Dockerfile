FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN useradd --create-home --uid 1000 appuser && \
    mkdir -p /app/data /app/certs && \
    chown -R appuser:appuser /app/data /app/certs

ARG INSTALL_DEV=true
COPY requirements*.txt ./
RUN if [ "${INSTALL_DEV}" = "true" ] && [ -f requirements-dev.txt ]; then \
      pip install --no-cache-dir -r requirements-dev.txt; \
    elif [ -f requirements.txt ]; then \
      pip install --no-cache-dir -r requirements.txt; \
    fi

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import ssl, urllib.request; urllib.request.urlopen('https://localhost:8000/health', context=ssl._create_unverified_context())" || exit 1

ENTRYPOINT ["sh", "scripts/entrypoint.sh"]
