# Multi-platform base image for Red Hat OpenShift
FROM python:3.11-slim

# Set environment variables for OpenShift
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

# Copy application files
COPY . /app

# Red Hat OpenShift Security: Grant root group (GID 0) write permissions
# OpenShift runs containers under arbitrary random UIDs with GID 0.
RUN chgrp -R 0 /app && \
    chmod -R g=u /app && \
    chmod -R 777 /app

# Expose standard OpenShift non-root HTTP port
EXPOSE 8080

# Run server
CMD ["python", "server.py"]
