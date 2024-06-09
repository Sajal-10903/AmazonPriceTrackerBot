import requests
from bs4 import BeautifulSoup
from twilio.rest import Client
from urllib.parse import urlparse
import time
import re
import random
import os
import logging  # For logging errors and successes

# Logging setup (optional)
logging.basicConfig(filename='price_tracker.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load Twilio credentials from environment variables
account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
twilio_phone_number = os.environ.get('TWILIO_PHONE_NUMBER')
your_phone_number = os.environ.get('YOUR_PHONE_NUMBER')

# Check if credentials are set
def send_whatsapp_message(message):
    """Sends a WhatsApp message using Twilio."""
    try:
        message = client.messages.create(
            body=message,
            from_='whatsapp:' + twilio_phone_number,
            to='whatsapp:' + your_phone_number
        )
        print("WhatsApp message sent:", message.sid)
    except Exception as e:  # Catch all exceptions to prevent crashes
        print(f"Error sending WhatsApp message: {e}")

def fetch_and_notify_price(product_url, desired_price, retry_count=0):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    max_retries = 3

    try:
        if "amazon.in" not in product_url:
            raise ValueError("This script is designed for Amazon.in URLs only.")

        response = requests.get(product_url, headers=headers)
        response.raise_for_status() 
        soup = BeautifulSoup(response.content, 'html.parser')

        # Amazon.in price extraction (prioritizing deal price)
        price_element = soup.find(id="priceblock_dealprice")
        if not price_element:  
            price_element = soup.find(id="priceblock_ourprice")
        if not price_element:
            price_element = soup.find(class_="a-offscreen")

        if price_element:
            price_text = price_element.get_text(strip=True)
            price_match = re.search(r'₹(\d+[\.,]\d+)', price_text)
            if price_match:
                price = float(price_match.group(1).replace(',', ''))

                if price <= desired_price:
                    message = f"Price dropped for {product_url}! Current price is ₹{price:.2f}"
                    send_whatsapp_message(message)
                    return True  # Indicate that the price was reached
                else:
                    print(f"Current price for {product_url} is ₹{price:.2f}, which is higher than your desired price of ₹{desired_price:.2f}.")
            else:
                raise ValueError("Price not found")
        else:
            raise ValueError(f"Price information not found for {product_url}")

    except requests.exceptions.RequestException as e:
        if isinstance(e, requests.exceptions.HTTPError) and e.response.status_code == 429 and retry_count < max_retries:
            delay = random.uniform(10, 30)
            print(f"Rate limited. Retrying after {delay:.2f} seconds...")
            time.sleep(delay)
            fetch_and_notify_price(product_url, desired_price, retry_count + 1)

def main():  
    product_url = input("Enter Amazon.in product URL: ")
    try:
        desired_price = float(input("Enter desired price: ₹"))
    except ValueError:
        print("Invalid price. Please enter a number.")
        return  # Exit if price is invalid

    while True:
        if fetch_and_notify_price(product_url, desired_price):
            break  # Exit loop if price is reached
        time.sleep(10)

if __name__ == "__main__":
    main()