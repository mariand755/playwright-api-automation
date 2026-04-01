
# Official Playwright image with Python support
FROM mcr.microsoft.com/playwright/python:v1.58.0-noble

# Set the working directory in the container
WORKDIR /app

# Copy the dependency file first to the container
COPY  requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project to the container
COPY . .  

# Default command runs the automated test suite.
CMD ["pytest", "-v"]