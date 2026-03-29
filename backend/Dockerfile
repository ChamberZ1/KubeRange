# [software: python, variant: 3.12-slim]
FROM python:3.12-slim

# Create and set working directory in the container to /app. All subsequent commands will run in this directory.
WORKDIR /app

# Install shared package first (build context is project root)
COPY shared/ /shared/
RUN pip install --no-cache-dir /shared/

# Install backend dependencies, skipping the local shared reference
COPY backend/requirements.txt .
RUN grep -v 'shared' requirements.txt | pip install --no-cache-dir -r /dev/stdin

# After installing dependencies, copy the rest of the backend code to the container.
COPY backend/app/ ./app/

# The command that runs when the container starts. 
# Use uvicorn to serve the FastAPI app on port 8000.
# Accessible from any network interface (without this, it would only be accessible from within the container).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
