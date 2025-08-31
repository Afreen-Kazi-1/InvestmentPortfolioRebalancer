# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port 5000 for the Flask app
EXPOSE 5000

# Command to run the application (Gunicorn is specified in docker-compose.yml)
# CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]