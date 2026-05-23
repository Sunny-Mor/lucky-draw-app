# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy the Flask application to the container
COPY pick_winner.py /app/app.py

# Copy requirements.txt if you want to separate dependencies (optional)
# COPY requirements.txt /app
# RUN pip install -r requirements.txt

# Install necessary packages
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir flask psycopg2-binary

# Set environment variables for Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# Expose the application port
EXPOSE 5000

# Run the application
CMD ["flask", "run"]
