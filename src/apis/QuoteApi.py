import requests
from utils.helpers import get_logger

logger = get_logger(__name__)

QUOTES_API_URL = "https://www.zohoapis.ca/crm/v2/Transport_Offers"

DEALS_MODULE_URL = "https://www.zohoapis.ca/crm/v2/Deals"
## Request Header
def get_header(token : str, content_type : str) -> dict:

    return {
        "Authorization": f"Zoho-oauthtoken {token}",
        "Content-Type": content_type,
    }
def create_quotes(token,data):
    try:
        headers = get_header(token, "application/json")

        data = {
            "data":data
        }

        response = requests.post(QUOTES_API_URL, headers=headers, json=data)
        logger.info(f"CREATE QUOTES RESPONSE : {response.json()}")
        return response
    
    except Exception as e:
        logger.error(f"Error creating Quotes: {e}")
        return {"message": "Error creating Quotes","error": str(e)}   
    
def update_quote(token : str, new_data : dict) -> dict:

    headers = get_header(token, "application/json")

    try:
        payload = {"data": [new_data]}
        response = requests.patch(QUOTES_API_URL, headers=headers, json=payload)
        logger.info(f"UPDATE QUOTES RESPONSE : {response.json()}")
        return response.json()
    
    except Exception as e:
        logger.error(f"Error Updating Quotes: {e}")

        return {"message": "Error Updating Quotes","error": str(e)}
    

def update_deal(token : str, new_data : dict) -> dict:

    headers = get_header(token, "application/json")
    try:
        payload = {"data": [new_data]}
        response = requests.patch(DEALS_MODULE_URL, headers=headers, json=payload)
        logger.info(f"UPDATE DEAL RESPONSE : {response.json()}")
        return response.json()
    
    except Exception as e:
        logger.error(f"Error Updating Deal: {e}")

        return {"message": "Error Updating Deal","error": str(e)}