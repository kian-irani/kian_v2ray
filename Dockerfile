# KIAN V2Ray web panel image (phase 7).
# Multi-stage kept simple: the panel is pure-Python + a few wheels.
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    KIAN_DB_PATH=/data/kian.db

WORKDIR /app

# Install only the panel's runtime deps (data layer is stdlib).
COPY panel/requirements.txt /app/panel/requirements.txt
RUN pip install --no-cache-dir -r panel/requirements.txt

# Copy the code the panel needs at runtime.
COPY core/ /app/core/
COPY panel/ /app/panel/

VOLUME ["/data"]
EXPOSE 8443

# Drop privileges.
RUN useradd --system --uid 10001 kian && mkdir -p /data && chown kian /data
USER kian

CMD ["uvicorn", "panel.main:app", "--host", "0.0.0.0", "--port", "8443"]
