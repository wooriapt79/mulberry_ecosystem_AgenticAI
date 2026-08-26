FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN addgroup --system mulberry && adduser --system --ingroup mulberry mulberry
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY luna ./luna
COPY alembic.ini .
COPY migrations ./migrations
USER mulberry
EXPOSE 8088
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8088} --no-access-log"]
