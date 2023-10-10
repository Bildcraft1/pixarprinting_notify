# Use the official Python image as the base image
FROM python:3-slim

# Set environment variables (if necessary)
ENV API_ID=123456
ENV API_HASH=123456
ENV BOT_ID=123456

# Set the working directory in the container
WORKDIR /bot

# Copy the local script and requirements file to the container
COPY main.py /bot/
COPY requirements.txt /bot/

# Install necessary packages and Chromium
RUN apt-get update && \
    apt-get install -y wget unzip curl gnupg && \
    wget -q https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/117.0.5938.149/linux64/chromedriver-linux64.zip && \
    unzip chromedriver-linux64.zip && \
    cd chromedriver-linux64 && \
    mv chromedriver /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver && \
    cd .. && \
    rm chromedriver-linux64.zip && \
    curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64]  http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list && \
    apt-get -y update && \
    apt-get -y install google-chrome-stable && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the display environment variable (for headless mode)
ENV DISPLAY=:99

# Command to run the script
CMD ["python", "./main.py"]
