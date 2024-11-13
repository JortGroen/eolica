# Use the official Python 3.12 slim image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy the pyproject.toml and poetry.lock files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry lock --no-update
RUN poetry install --no-root

# Copy the rest of the application code
COPY . .

# Command to run your application
CMD ["python", "eolica.py"]