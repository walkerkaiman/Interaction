# Docker container for running Interaction Framework tests
FROM python:3.9-slim

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy the application code
COPY . .

# Create a non-root user for running tests
RUN useradd -m -u 1000 testuser && chown -R testuser:testuser /app
USER testuser

# Default command runs validation
CMD ["python", "tests/validate_setup.py"]