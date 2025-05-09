FROM python:3.11-slim

# Install Tkinter and dependencies
RUN apt-get update && apt-get install -y \
    python3-tk \
    libsqlite3-dev \
    tk \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy code
COPY src/ /app/

# Create Streamlit config directory
RUN mkdir -p /root/.streamlit

# Copy custom config file
COPY config.toml /root/.streamlit/config.toml

# Install Python dependencies
COPY requirements.txt .
RUN mkdir -p /root/.streamlit
COPY config.toml /root/.streamlit/config.toml
COPY secrets.toml /root/.streamlit/secrets.toml
RUN  pip install --no-cache-dir -r requirements.txt
#RUN pip install python 
# Set display environment (headless safe default)
ENV DISPLAY=:0
RUN apt-get update && apt-get install -y python3-tk
# Entry point
#CMD ["python", "main.py"]
# Expose Streamlit port
EXPOSE 8501

# Run the Streamlit app (replace with your main file if renamed)
#CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.enableCORS=false", "--browser.gatherUsageStats=false"]
CMD ["streamlit", "run", "main_v3.py", "--server.port=8501", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]