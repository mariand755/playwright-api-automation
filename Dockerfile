
# Official Playwright image with Python support
FROM mcr.microsoft.com/playwright/python:v1.60.0-noble

# Set the working directory in the container
WORKDIR /app

# Upgrade OS packages to remediate fixable base-image CVEs before installing project deps
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
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
