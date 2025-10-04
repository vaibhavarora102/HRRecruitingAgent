FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and application files
COPY requirements.txt .
COPY . .

# Install Python dependencies
RUN pip3 install -r requirements.txt

# Create a startup script to handle secrets and port configuration
RUN echo '#!/bin/bash\n\
# Handle Docker secrets\n\
if [ -f "$EMAIL_USER_FILE" ]; then\n\
    export EMAIL_USER=$(cat "$EMAIL_USER_FILE")\n\
fi\n\
if [ -f "$EMAIL_PASSWORD_FILE" ]; then\n\
    export EMAIL_PASSWORD=$(cat "$EMAIL_PASSWORD_FILE")\n\
fi\n\
if [ -f "$CEREBRAS_API_KEY_FILE" ]; then\n\
    export CEREBRAS_API_KEY=$(cat "$CEREBRAS_API_KEY_FILE")\n\
fi\n\
# Use PORT environment variable if available, otherwise default to 8501\n\
export STREAMLIT_SERVER_PORT=${PORT:-8501}\n\
export STREAMLIT_SERVER_ADDRESS=0.0.0.0\n\
exec streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0' > /app/start.sh && \
    chmod +x /app/start.sh

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:${PORT:-8501}/_stcore/health

ENTRYPOINT ["/app/start.sh"]