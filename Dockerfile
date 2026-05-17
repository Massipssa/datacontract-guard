FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DATA_CONTRACT_ENV=container
ENV DATA_CONTRACT_ALLOWED_ROOTS=/app

COPY . .

RUN pip install --no-cache-dir .

EXPOSE 8093

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8093"]
