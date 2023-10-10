#!/usr/bin/env python
import asyncio
import logging

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from telethon import TelegramClient, Button
from selenium.webdriver.chrome.options import Options

import os
from dotenv import load_dotenv

load_dotenv()

# Define your Telegram API credentials
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

last_id = None

# Define CSS selectors
pixart_hhpage_deals_css_selector = "div.col-6.col-sm-3.gallery_item.promo_hour_btn"
pixart_deal_name_css_selector = ".gallery_item_name"
pixart_deal_price_css_selector = ".gallery_discount"
pixart_deal_sold_out_css_selector = ".sold_out_label"


def check_pixar_hour() -> bool:
    options = Options()
    options.headless = True
    options.add_argument("--disable-gpu")  # Optional, if applicable to your environment
    driver = webdriver.Chrome(options=options)
    try:
        # Navigate to the page
        driver.get("https://www.pixartprinting.it/happy-hour")

        # Locate the element using the class name
        promo_status_element = driver.find_element(By.CSS_SELECTOR, '.promo-hour-off')

        # Get the 'style' attribute value
        style_attribute = promo_status_element.get_attribute('style')

        # Check the 'style' attribute for 'display: none'
        if 'display: none' in style_attribute:
            return True
        else:
            return False
    finally:
        # Clean up
        driver.quit()


def get_discounted_items() -> list:
    options = Options()
    options.headless = True
    options.add_argument("--disable-gpu")  # Optional, if applicable to your environment
    driver = webdriver.Chrome(options=options)
    try:
        driver.get("https://www.pixartprinting.it/birthday/")

        # Extract deal elements
        deals = driver.find_elements(By.CSS_SELECTOR, pixart_hhpage_deals_css_selector)
        parsed_deals = []

        for deal in deals:
            try:
                name = deal.find_element(By.CSS_SELECTOR, pixart_deal_name_css_selector).text.strip()
                price = deal.find_element(By.CSS_SELECTOR, pixart_deal_price_css_selector).text.strip()

                sold_out_elements = deal.find_elements(By.CSS_SELECTOR, pixart_deal_sold_out_css_selector)
                sold_out = len(sold_out_elements) > 0

                deal_url = ''
                if not sold_out:
                    deal_url = deal.find_element(By.TAG_NAME, "a").get_attribute("href")

                if name and not price.endswith('%'):
                    parsed_deals.append({
                        "name": name,
                        "price": price,
                        "sold_out": sold_out,
                        "deal_url": deal_url
                    })
            except NoSuchElementException as e:
                print(f"Exception caught while parsing the scraped item: {e}")

        logger.log(logging.INFO, f"Found {len(parsed_deals)} discounted items")
        logger.log(logging.INFO, f"Discounted items: {parsed_deals}")
        return parsed_deals
    finally:
        driver.quit()


async def send_message(client, discounted_items) -> int:
    # Filter out deals with invalid URLs
    valid_discounted_items = [deal for deal in discounted_items if deal["deal_url"]]

    message_text = (
        "**L'HAPPY HOUR è INIZIATA**\n\n"
        "[Pixar Printing](https://www.pixartprinting.it/happy-hour/)\n\n"
        "Offerte Sold Out:\n"
        "Offerte valide fino alle 18:00"
    )

    # Create buttons only for deals with valid URLs
    buttons = [
        [Button.url(f'{deal["name"]} - {deal["price"]}', deal["deal_url"])]
        for deal in valid_discounted_items
    ]

    await client.send_message('@pixarprintingnotify', "**TESTING MODE**")
    message = await client.send_message('@pixarprintingnotify', message_text, buttons=buttons)
    return message.id  # Return the message ID


async def update_message(client, message_id: int, sold_out_item: str) -> None:
    logger.log(logging.INFO, f"Updating message {message_id} to mark {sold_out_item} as sold out")
    try:
        # Get the current message
        message = await client.get_messages('@pixarprintingnotify', ids=message_id)
        current_buttons = message.reply_markup.rows if message.reply_markup else []

        # Initialize an empty list to keep track of the sold-out offers
        sold_out_offers = []

        # Initialize an empty list for the updated buttons
        updated_buttons = []

        # Iterate through each row of buttons in the current message
        for row in current_buttons:
            new_row = []  # Initialize an empty list for the new row
            for button in row.buttons:
                item_text = button.text
                # Change this line to check for containment instead of exact match
                if sold_out_item in item_text:
                    sold_out_offers.append(item_text)
                else:
                    new_row.append(button)  # Otherwise, keep the button in the new row
            if new_row:  # If the new row is not empty, append it to the updated_buttons
                updated_buttons.append(new_row)

        # Format the updated sold out offers text
        sold_out_text = '\n'.join(f"- {offer}" for offer in sold_out_offers)

        # Construct the updated message text
        updated_message_text = (
            "**L'HAPPY HOUR è INIZIATA**\n\n"
            "[Pixar Printing](https://www.pixartprinting.it/happy-hour/)\n\n"
            "Offerte Sold Out:\n"
            f"{sold_out_text}\n\n"
            "Offerte valide fino alle 18:00"
        )

        # Edit the message with the updated information
        await client.edit_message('@pixarprintingnotify', message_id, text=updated_message_text,
                                  buttons=updated_buttons)
    except Exception as e:
        logger.log(logging.ERROR, f"Error updating message: {e}")


async def monitor_discounted_items(client, message_id, original_items):
    while True:
        # Check if the Happy Hour is still active
        pixar_hour_status = await asyncio.get_event_loop().run_in_executor(None, check_pixar_hour)
        if not pixar_hour_status:
            logger.log(logging.INFO, "Happy Hour has ended. Stopping monitoring.")
            break  # Exit the loop if Happy Hour has ended

        # Get the updated list of discounted items
        updated_items = get_discounted_items()

        # Find items that have gone sold out
        for original_item in original_items:
            original_name = original_item["name"]
            original_price = original_item["price"]
            found = False
            for updated_item in updated_items:
                updated_name = updated_item["name"]
                updated_price = updated_item["price"]
                if original_name == updated_name and original_price == updated_price:
                    found = True
                    break
            if not found:
                # If an item is no longer in the updated list, it has gone sold out
                sold_out_item = f'{original_name} - {original_price}'
                await update_message(client, message_id, sold_out_item)

        # Update the original_items list to reflect the current state of the website
        original_items = updated_items

        # Wait for a while before checking again (e.g., wait for 5 minutes)
        await asyncio.sleep(300)


async def main() -> None:
    global last_id

    client = TelegramClient('bot', api_id, api_hash)
    await client.start(bot_token=bot_token)
    try:
        while True:  # This creates an infinite loop
            loop = asyncio.get_event_loop()
            pixar_hour_status = await loop.run_in_executor(None, check_pixar_hour)

            if pixar_hour_status:
                logger.log(logging.INFO, "Pixar Hour started")
                original_items = get_discounted_items()
                last_id = await send_message(client, original_items)
                await monitor_discounted_items(client, last_id, original_items)
            else:
                logger.log(logging.INFO, "Pixar Hour not started yet")

            # Wait for 1 hour before checking again
            await asyncio.sleep(20)
    finally:
        await client.disconnect()

if __name__ == '__main__':
    print("Starting...")
    print("Bot token: " + bot_token)
    asyncio.run(main())
