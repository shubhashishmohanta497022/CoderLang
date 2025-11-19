# 1. Set the base image
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the requirements file first
COPY requirements.txt .

# 4. Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your application code
COPY . .

# 6. Expose the port for Streamlit
EXPOSE 8501

# 7. Healthcheck to ensure the container is running correctly
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# 8. Set the default command to run the Streamlit Dashboard
# We bind to 0.0.0.0 so it is accessible outside the container
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]