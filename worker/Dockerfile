# [software: python, variant: 3.12-slim]
FROM python:3.12-slim

# Set working dir.
WORKDIR /app

# Install shared package first (build context is project root)
COPY shared/ /shared/
RUN pip install --no-cache-dir /shared/

# Install worker dependencies, skipping the local shared reference
COPY worker/requirements.txt .
RUN grep -v 'shared' requirements.txt | pip install --no-cache-dir -r /dev/stdin

COPY worker/app/ ./app/

CMD ["python", "app/worker.py"]
