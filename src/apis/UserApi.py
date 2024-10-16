
import requests
from utils.helpers import *

logger = get_logger(__name__)

CARRIER_URL= "https://www.zohoapis.ca/crm/v2/Carrier"



def add_carrier(access_token :str, carriers : dict):
    """ Add a carrier to Zoho CRM"""

    
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json",
    }
    response = requests.post(CARRIER_URL, headers=headers, json=carriers)

    if response.status_code == 201:

        carrier_id = response.json()["data"]["id"]


def add_contact(access_token :str, contacts : dict):
    """ Add a contact to Zoho CRM"""
    
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json",
    }
    response = requests.post(CARRIER_URL, headers=headers, json = contacts  )

    if response.status_code == 201:

        carrier_id = response.json()["data"]["id"]