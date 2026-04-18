# Stage 1: Clone the repository (Bust cache for Persistence Fix)
FROM alpine/git AS cloner
WORKDIR /repo
RUN git clone https://github.com/AlexaInc/tgchannel24x7.git . && git reset --hard origin/master # V1.1.1

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
    libffi-dev \
    gcc \
    g++ \
    git \
    nodejs \
    unzip \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Setup persistent global cache for yt-dlp remote components
RUN mkdir -p /app/yt-dlp-cache && chmod -R 777 /app/yt-dlp-cache
ENV XDG_CACHE_HOME=/app/yt-dlp-cache

# Install Deno (yt-dlp's preferred JS runtime)
RUN curl -fsSL https://deno.land/x/install/install.sh | sh
ENV DENO_INSTALL="/root/.deno"
ENV PATH="$DENO_INSTALL/bin:$PATH"

# Force a rebuild of requirements (Cache Buster)
RUN echo "Rebuild Version: 1.0.5" > /rebuild_tag.txt

# Copy python requirements and install
COPY --from=cloner /repo/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir tgcrypto
RUN pip uninstall -y yt-dlp-youtube-oauth2 || true

# Ensure nodejs is mapped to 'node' so yt-dlp can find it for scrambling challenges
RUN ln -s /usr/bin/nodejs /usr/bin/node || true

# Pre-download yt-dlp remote components to the persistent cache
# Note: we use --cache-dir explicitly to match the runtime config
RUN yt-dlp --remote-components ejs:github --update-remote-components --quiet --cache-dir /app/yt-dlp-cache || true

# Copy the rest of the backend code
COPY --from=cloner /repo/ . 

# Copy the built frontend
COPY --from=frontend-builder /app/web/dist ./web/dist

# Final touches and permissions
RUN chmod +x entrypoint.sh

# Run the unified app via entrypoint
CMD ["/bin/sh", "entrypoint.sh"]
