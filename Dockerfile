FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY artifacts/models ./artifacts/models

RUN pip install --no-cache-dir .

EXPOSE 8000
CMD ["uvicorn", "last_price.api:app", "--host", "0.0.0.0", "--port", "8000"]
