FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system konvertira && adduser --system --ingroup konvertira konvertira

RUN apt-get update \
    && apt-get install -y --no-install-recommends libreoffice-writer libreoffice-calc libreoffice-impress fonts-dejavu-core libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/collect_pdf_notices.py ./scripts/collect_pdf_notices.py
RUN python scripts/collect_pdf_notices.py /usr/share/konvertira/pdf-notices --debian-runtime \
    && chmod -R a+rX /usr/share/konvertira/pdf-notices

COPY config.py main.py mcp_server.py ./
COPY format_registry.json ./
COPY backend ./backend
COPY konvertira_mcp ./konvertira_mcp
COPY scripts/prepare_background_model.py ./scripts/prepare_background_model.py
COPY scripts/check_background_model_permissions.py ./scripts/check_background_model_permissions.py
ENV BACKGROUND_MODEL_DIR=/opt/konvertira-models
RUN python scripts/prepare_background_model.py
COPY docs/licenses/U2NET-Apache-2.0.txt /opt/konvertira-models/LICENSE-U2NET.txt
COPY docs/background-removal.md /opt/konvertira-models/ATTRIBUTION.md

RUN chmod 0555 /opt/konvertira-models \
    && chmod 0444 /opt/konvertira-models/*

RUN mkdir -p /tmp/konvertira-results /tmp/konvertira-mcp-results \
    && chown -R konvertira:konvertira /app /tmp/konvertira-results /tmp/konvertira-mcp-results

USER konvertira

RUN python scripts/check_background_model_permissions.py

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
