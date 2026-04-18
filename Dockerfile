# Stage 1: Build the frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/web
COPY web/package*.json ./
RUN npm install
COPY web/ ./
RUN npm run build

# Stage 2: Run the bot and backend
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code
COPY . .

# Copy the built frontend from stage 1
COPY --from=frontend-builder /app/web/dist ./web/dist

# Expose the port (Hugging Face uses 7860)
EXPOSE 7860

# Run the unified app
CMD ["python", "main.py"]
