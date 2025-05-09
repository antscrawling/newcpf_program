FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies in one layer
RUN apt-get update && \
    apt-get install -y libglib2.0-0 libsm6 libxext6 libxrender-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app code
COPY src/ /app/

# Set up Streamlit config and secrets
RUN mkdir -p /root/.streamlit
COPY config.toml /root/.streamlit/config.toml
COPY secrets.toml /root/.streamlit/secrets.toml

# Expose the Streamlit port
EXPOSE 8501

# Run the Streamlit app
CMD ["streamlit", "run", "main_v2.py", "--server.port=8501", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]