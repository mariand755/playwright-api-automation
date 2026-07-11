
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
# --break-system-packages: required because the base image's OS packages now enforce
# PEP 668 (externally-managed-environment); this container is single-purpose and ephemeral,
# so installing into the system Python here carries no real risk.
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# Copy the rest of the project to the container
COPY . .

# Default command runs the automated test suite.
CMD ["pytest", "-v"]
