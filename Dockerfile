# -------------------------------------------------------------
# Stage 1: Build React/Vite Frontend
# -------------------------------------------------------------
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# -------------------------------------------------------------
# Stage 2: Production Python / FastAPI Service
# -------------------------------------------------------------
FROM python:3.11-slim

# Install system dependencies for GDAL/Rasterio and OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements (CPU torch first to save 2.5GB disk and 10 mins on Render)
COPY requirements.txt .
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

# Copy backend, model weights, and sample test rasters
COPY backend/ ./backend/
COPY runs/ ./runs/
COPY samples/ ./samples/

# Copy compiled frontend from Stage 1 builder
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose default port
EXPOSE 8000

ENV PYTHONUNBUFFERED=1

# Cloud-native runner: listens on Render's $PORT dynamically, falls back to 8000 locally
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
