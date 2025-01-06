# utils/helpers.py
import re
import logging
import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


logger = logging.getLogger(__name__)

def standardize_name(name):
    name = name.title()  # Capitalize the first letter of each word
    # Remove punctuation except hyphens
    name = re.sub(r"[^\w\s-]", '', name)  # Keeps hyphens, removes other punctuation
    # Remove extra spaces
    name = re.sub(r'\s+', ' ', name)  # Replace multiple spaces with a single space
    name = name.strip()  # Remove leading and trailing spaces
    return name

# Function to configure logging
def get_logger(name):
    # Create a logger
    logger = logging.getLogger(name)
    
    # If the logger already has handlers, don't add more (this avoids duplicate logs)
    if not logger.hasHandlers():
        # Set logging level
        logger.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter and add it to the handler
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        
        # Add the console handler to the logger
        logger.addHandler(console_handler)
    
    return logger

def send_message_to_channel(bot_token, channel_id, message):
    client = WebClient(token=bot_token)

    try:
        response = client.chat_postMessage(
            channel=channel_id,
            text=message,
            unfurl_links=False,  # Disable link previews
    unfurl_media=False 
        )
        print(f"Message successfully sent to channel {channel_id} on Slack")
    except SlackApiError as e:
        print(f"Error sending Message to slack: {e}")


def manage_prv(url):
    if url.startswith("//"):
        url = "https:" + url
    else:
        return url

    return url


def get_header(token):

    headers = {
            "Authorization": f"Zoho-oauthtoken {token}",
            "Content-Type": "application/json",
        }

    return headers


def extract_tax_province(province_address):
    province_address = province_address.upper()  # Convert to lowercase for flexibility
    province_map = {
        "AB": "Alberta",
        "BC": "British Columbia",
        "MB": "Manitoba",
        "NB": "New Brunswick",
        "NL": "Newfoundland and Labrador",
        "NS": "Nova Scotia",
        "ON": "Ontario",
        "PE": "Prince Edward Island",
        "QC": "Quebec",
        "SK": "Saskatchewan",
        "NT": "Northwest Territories",
        "NU": "Nunavut",
        "YT": "Yukon"
    }
    # First check for full province name (in case it's already present in the address)
    for code, abbreviation in province_map.items():
        if abbreviation.upper() in province_address:
            return abbreviation.capitalize()  # Return the full name as a proper noun (capitalized)

    # Then check for province abbreviation (2-letter code)
    match = re.search(r"\b([A-Z]{2})\b", province_address)  # Regex looks for 2-letter province code
    
    if match:
        province_abbreviation = match.group(1)
        tax_province = province_map.get(province_abbreviation, "Unknown Province")
        return tax_province.capitalize()  # Return the province name corresponding to the abbreviation
    else:
        return "Unknown Province"

def normalize_text(text):
    if isinstance(text, str):
        return text.lower().strip().replace("é", "e")
    return text