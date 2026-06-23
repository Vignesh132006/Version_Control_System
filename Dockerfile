# Use official slim Python image
FROM python:3.10-slim

# Set working directory inside container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files to container
COPY . .

# Expose the port Flask runs on
EXPOSE 5000

# Set environment variables for production
ENV FLASK_ENV=production
ENV DB_HOST=localhost
ENV DB_USER=root
ENV DB_PASSWORD=Pinky@143
ENV DB_NAME=version_system

# Run database setup script and start the Gunicorn server
# Gunicorn binds to 0.0.0.0:5000
CMD ["sh", "-c", "python db_setup.py && gunicorn --bind 0.0.0.0:5000 wsgi:app"]
