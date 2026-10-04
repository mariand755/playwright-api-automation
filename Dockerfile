
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
# virtualenv ships with the base image but nothing here uses it (pip-audit uses stdlib venv);
# remove it (and its seed-wheel cache, which bundles a scannable copy of pip) after project
# installs so Trivy doesn't flag it (CVE-2026-102925/102930/102937).
# pip check fails the build if a future dependency actually requires virtualenv.
RUN python -m pip install --no-cache-dir --break-system-packages -r requirements.txt \
    && python -m pip uninstall -y --break-system-packages virtualenv \
    && rm -rf /root/.cache/virtualenv \
    && python -m pip check

# Copy the rest of the project to the container
COPY . .

# Default command runs the automated test suite.
CMD ["pytest", "-v"]
