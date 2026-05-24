FROM python:3.12-slim

# Create a non-root user and group
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Change ownership to the non-root user
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Expose port for Cloud Run
ENV PORT=8080
EXPOSE 8080

# Run with Gunicorn and Uvicorn workers
CMD ["gunicorn", "main:app", "--workers", "2", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080"]
