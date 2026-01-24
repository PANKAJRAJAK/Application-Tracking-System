FROM python:3.12-slim

# System deps
RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# App directory
WORKDIR /app

# Copy files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Streamlit config
EXPOSE 3000

CMD ["streamlit", "run", "app.py", "--server.port=3000", "--server.address=0.0.0.0"]