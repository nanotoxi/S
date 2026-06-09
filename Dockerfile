FROM python:3.11-slim

WORKDIR /app

# Install Node.js 20 for building the React frontend
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Build React frontend first
COPY web/package*.json ./web/
RUN cd web && npm ci --silent
COPY web/ ./web/
RUN cd web && npm run build

# Install Python dependencies
# torch needs a separate index URL for the CPU-only wheel
COPY requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN grep -v "^torch" requirements.txt | pip install --no-cache-dir -r /dev/stdin

# Copy application code
COPY . .

EXPOSE 8000
CMD ["python", "api_server.py"]
