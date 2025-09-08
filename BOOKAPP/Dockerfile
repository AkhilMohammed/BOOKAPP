FROM python:3.10-slim

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONBUFFERED=1

# Install required system tools and Python build tools
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    libpq-dev \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Pre-install pip build backends globally before any wheel building begins
RUN python -m pip install --upgrade pip setuptools wheel build

# Set work directory
WORKDIR /app

# Copy files
COPY . .

# Only now install requirements
RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
