
# Official Playwright image with Python support
FROM mcr.microsoft.com/playwright/python:v1.60.0-noble

# Set the working directory in the container
WORKDIR /app

# Install python3-venv so pip-audit can create isolated resolution environments
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3.12-venv \
    && rm -rf /var/lib/apt/lists/*

# Copy the dependency file first to the container
COPY  requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project to the container
COPY . .

# Default command runs the automated test suite.
CMD ["pytest", "-v"]
