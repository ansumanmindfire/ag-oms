# Builder Stage
FROM python:3.14-slim AS builder

WORKDIR /code

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry

# Copy dependency definition files
COPY pyproject.toml poetry.lock* ./

# Install production dependencies into system site-packages
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-root

# Runtime Stage
FROM python:3.14-slim AS runtime

WORKDIR /code

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copy installed site-packages and binaries from builder stage
COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create directories for data and logs
RUN mkdir -p logs data

# Copy application source code
COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

