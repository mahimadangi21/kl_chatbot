# Step 1: Build the React Frontend
FROM node:20-slim as build-stage
WORKDIR /ui
COPY ui/package*.json ./
RUN npm install
COPY ui/ ./
RUN npm run build

# Step 2: Setup the Python Backend
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Copy built frontend from build-stage to the location FastAPI expects
COPY --from=build-stage /ui/dist /app/ui/dist

# Expose port (Hugging Face uses 7860 by default for Spaces)
ENV PORT=7860
EXPOSE 7860

# Command to run the application
CMD ["python", "api.py"]
