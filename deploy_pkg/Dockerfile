# Stage 1: Build React
FROM node:20 AS build
WORKDIR /app
# Pre-install dependencies for better caching
COPY ui/package*.json ./ui/
RUN cd ui && npm install
# Build the app
COPY ui/ ./ui/
RUN cd ui && npm run build

# Stage 2: Backend
FROM python:3.11
WORKDIR /app

# Non-slim images have build-essential already, but we ensure requirements are met
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Copy built frontend
COPY --from=build /app/ui/dist /app/ui/dist

# Env and Port
ENV PORT=7860
EXPOSE 7860

# Force uvicorn to bind to 0.0.0.0
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "7860"]
