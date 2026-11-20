FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY config ./config

RUN useradd --create-home --shell /usr/sbin/nologin parser \
    && mkdir -p /app/output \
    && chown -R parser:parser /app
USER parser

CMD ["python", "-m", "src.cli", "--config", "config/parser.json"]
