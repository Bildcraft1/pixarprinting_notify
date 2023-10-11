# Use the official Python image as the base image
FROM python:3-slim

# Set environment variables (if necessary)
ENV API_ID=123456
ENV API_HASH=123456
ENV BOT_ID=123456
ENV CHANNEL_USERNAME=channel_username
ENV DEVELOPER_CHAT_ID=123456

# Set the working directory in the container
WORKDIR /bot

# Copy the local script and requirements file to the container
COPY main.py /bot/
COPY requirements.txt /bot/

# Install necessary packages and Chromium
RUN apt-get update && \
    apt-get install -y wget curl gnupg && \
    curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64]  http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list && \
    apt-get -y update && \
    apt-get -y install google-chrome-stable && \
    pip install --no-cache-dir -r requirements.txt chromedriver-autoinstaller && \
    python -c "import chromedriver_autoinstaller; chromedriver_autoinstaller.install()" && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the display environment variable (for headless mode)
ENV DISPLAY=:99

# Command to run the script
CMD ["python", "./main.py"]
