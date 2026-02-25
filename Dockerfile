# Hugging Face Spaces Dockerfile for BizIT Analytics Dashboard
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Create necessary directories
RUN mkdir -p backend/instance backend/uploads

# Set environment variables
ENV FLASK_APP=backend/app.py
ENV FLASK_ENV=production

# Expose port 7860 (required by Hugging Face Spaces)
EXPOSE 7860

# Run the Flask app on port 7860
CMD ["gunicorn", "--chdir", "backend", "app:app", "--bind", "0.0.0.0:7860"]
