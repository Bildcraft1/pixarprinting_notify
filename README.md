# Pixar Printing Notify Bot

> This is still in beta and will change

Pixar Printing Notify Bot is a bot used for automaticaly send to a Telegram Channel the
content of the Happy Hour on Pixar Pritning (Check the repo link for an example)

## How do i host this?

### Docker
You can use the docker image to run this bot, here you can find an example of the Docker compose

```yaml
version: '3'

services:
  bot:
    image: ghcr.io/bildcraft1/pixarprinting_notify:master
    hostname: pixar
    environment:
      - API_ID=<Your API ID>
      - API_HASH=<Your API HASH>
      - BOT_TOKEN=<Your bot token>
      - CHANNEL_USERNAME=<Your chat username>
      - DEVELOPER_CHAT_ID=<your chat id with the bot>
    restart: unless-stopped
```

### Manual way
1. Download the source code
2. Install the required dependencies with pip (install the requirements.txt file)
3. Create a .env file based of the example and put your data
4. Run the bot using Python

## Credits

[Pixarto](https://github.com/MrTriad/pixarto) for the CSS classes

