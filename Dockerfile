# Stage 1: Build frontend
FROM node:20-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ .
RUN VITE_API_URL="" npm run build

# Stage 2: Python backend + built frontend
FROM python:3.12-slim
WORKDIR /app

# Install Python deps
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy application code
COPY backend/ backend/

# Copy built frontend from stage 1
COPY --from=frontend /app/frontend/dist frontend/dist

EXPOSE 8081
WORKDIR /app/backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8081"]
