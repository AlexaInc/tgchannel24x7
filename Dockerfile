# Stage 1: Clone the repository
FROM alpine/git AS cloner
WORKDIR /repo
RUN git clone https://github.com/AlexaInc/tgchannel24x7.git .

# Stage 2: Build the frontend (Node stage is already cached usually)
FROM node:20-alpine AS frontend-builder
WORKDIR /app/web
COPY --from=cloner /repo/web/package*.json ./
RUN npm install
COPY --from=cloner /repo/web/ ./
RUN npm run build

# Stage 3: Run the bot and backend
FROM python:3.11-slim
WORKDIR /app

# Optimize Apt-get: No-install-recommends and cleanup
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    python3-dev \
    libssl-dev \
    git \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Force a rebuild of requirements
RUN echo "Rebuild Date: 2026-04-18" > /rebuild_tag.txt

# Copy python requirements and install
COPY --from=cloner /repo/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code
COPY --from=cloner /repo/ . 

# Copy the built frontend
COPY --from=frontend-builder /app/web/dist ./web/dist

# Expose the port
EXPOSE 7860

# Run the unified app
CMD ["python", "main.py"]
