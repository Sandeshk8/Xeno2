# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (build-essential for potential C-extensions)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# We use volumes for persistent data (database and config)
# This way, you can update the code without losing your DB
VOLUME ["/app/database", "/app/word_chain_data"]

# Run the bot
CMD ["python", "bot.py"]
