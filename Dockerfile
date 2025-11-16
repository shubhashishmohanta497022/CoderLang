# 1. Set the base image
# This tells Docker to start with a slim version of Python 3.11
FROM python:3.11-slim

# 2. Set the working directory inside the container
# All our commands will run from /app
WORKDIR /app

# 3. Copy the requirements file first
# This is done as a separate step for better Docker caching
COPY requirements.txt .

# 4. Install the Python dependencies
# This reads requirements.txt and installs the packages
RUN pip install -r requirements.txt

# 5. Copy the rest of your application code
# This copies main.py, agents/, orchestrator/, etc. into /app
COPY . .

# 6. Set the default command
# This is the command that runs when the container starts
CMD ["python", "main.py"]