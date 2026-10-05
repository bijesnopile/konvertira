FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system konvertira && adduser --system --ingroup konvertira konvertira

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY config.py main.py mcp_server.py ./
COPY backend ./backend
COPY konvertira_mcp ./konvertira_mcp

RUN mkdir -p /tmp/konvertira-results /tmp/konvertira-mcp-results \
    && chown -R konvertira:konvertira /app /tmp/konvertira-results /tmp/konvertira-mcp-results

USER konvertira

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
