# Using slim images for ultra-fast Zero-Torch build
FROM node:20-slim AS build
WORKDIR /app
COPY ui/package*.json ./ui/
RUN cd ui && npm install
COPY ui/ ./ui/
RUN cd ui && npm run build

FROM python:3.11-slim
WORKDIR /app

# Only need libgl1 for Faiss (very light)
RUN apt-get update && apt-get install -y libgl1 && rm -rf /var/lib/apt/lists/*

# Fix: Hugging Face specific UID/GID permissions
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH
WORKDIR /home/user/app

# Install light requirements
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code and built frontend
COPY --chown=user . .
COPY --from=build /app/ui/dist /app/ui/dist

ENV PORT=7860
EXPOSE 7860

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "7860"]
