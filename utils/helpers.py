import re
import logging
import datetime


def standardize_name(name):
    name = name.title()
    # Remove punctuation
    name = re.sub(r'[^\w\s]', '', name)
    # Remove extra spaces
    name = name.strip()
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


def format_datetime(date_str):
    try:
        # Parse the datetime string (assuming it might include milliseconds or timezone info)
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00').split('.')[0])
        # Convert it to the required format
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        # Handle the case where date_str is not in the expected format
        return None