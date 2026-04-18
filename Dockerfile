# Stage 1: Clone the repository
FROM alpine/git AS cloner
WORKDIR /repo
# Hardcoded repository URL for AlexaInc/tgchannel24x7
RUN git clone https://github.com/AlexaInc/tgchannel24x7.git .

# Stage 2: Build the frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/web
COPY --from=cloner /repo/web/package*.json ./
RUN npm install
COPY --from=cloner /repo/web/ ./
RUN npm run build

# Stage 3: Run the bot and backend
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy python requirements and install
COPY --from=cloner /repo/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code from cloned repo
COPY --from=cloner /repo/ . 

# Copy the built frontend from stage 2
COPY --from=frontend-builder /app/web/dist ./web/dist

# Expose the port (Hugging Face uses 7860)
EXPOSE 7860

# Run the unified app
CMD ["python", "main.py"]
