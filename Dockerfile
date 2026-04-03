FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Data volume mount point
RUN mkdir -p /data

ENV DB_PATH=/data/ejar.db
ENV SECRET_KEY=change-this-secret-in-production
ENV ADMIN_USERNAME=admin
ENV ADMIN_PASSWORD=admin123

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
