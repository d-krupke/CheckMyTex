FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    aspell \
    aspell-en \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install CheckMyTex
COPY .. /checkmytex
RUN pip install --no-cache-dir /checkmytex

# Copy web app
COPY . /app

# Install web app dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 5000

# Run the app
CMD ["python", "app.py"]
