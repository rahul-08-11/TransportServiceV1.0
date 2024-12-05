import requests
from utils.helpers import get_logger

logger = get_logger(__name__)

QUOTES_API_URL = "https://www.zohoapis.ca/crm/v2/Transport_Offers"


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
    