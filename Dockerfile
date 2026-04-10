# Ultra-simple: React is pre-built locally, only Python needed here
FROM python:3.11-slim

WORKDIR /app

# Minimal system dependency
RUN apt-get update && apt-get install -y libgomp1 && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files (including pre-built ui/dist)
COPY . .

# Hugging Face requires UID 1000
RUN useradd -m -u 1000 user && chown -R user /app
USER user

ENV PORT=7860
EXPOSE 7860

CMD ["python", "api.py"]
