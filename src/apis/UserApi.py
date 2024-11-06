import requests
from utils.helpers import *

logger = get_logger(__name__)

CARRIER_URL= "https://www.zohoapis.ca/crm/v2/Carrier"



def add_bubble_carrier(access_token :str, carriers : dict):
    """ Add a carrier to Zoho CRM"""

    
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json",
    }

    payload = {"data": [carriers]}
    response = requests.post(CARRIER_URL, headers=headers, json=payload)

    return response


def add_carrier_contact(access_token : str,contact_data : dict):
            ## endpoint to add contacts
    url = "https://www.zohoapis.ca/crm/v2/Contacts"

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }


        # Create the 'data' list with the dictionary
    data = {"data": [contact_data]}
    response = requests.post(url, headers=headers, json=data)
    try:
        
        if response.status_code in [200,201]:
            data = response.json()
            contact_id = response.json()["data"][0]["details"]["id"]
        else:
            logger.warning(f"Failed to add contact. Status code: {response.json()}")
            contact_id = ''

        return contact_id

    except requests.exceptions.RequestException as e:
        logger.error(f"Error adding contact: {e}")
        return ''

## Add Companies registered through the bubble App
def add_bubble_Customer(access_token,company_data):
    url = "https://www.zohoapis.ca/crm/v2/Accounts"
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }

    payload = {"data": [company_data]}
    
    response = requests.post(url, headers=headers, json=payload)
    logger.info(response.json())
    return response

def link_contact_to_company_id(access_token, company_id, contact_id):
    url = "https://www.zohoapis.ca/crm/v2/contactsxcompanies"

    # Authorization header
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "data": [
            {
                "Companies": company_id,  # Use contact record ID
                "Company": contact_id   # Use company record ID
            }
        ]
    }
    response = requests.post(url, headers=headers, json=payload)
    return response



def add_customer_contact(access_token : str,contact_data,Account_ID):
        ## endpoint to add contacts
    url = "https://www.zohoapis.ca/crm/v2/Contacts"

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }


        # Create the 'data' list with the dictionary

    contact_data['Dealership'] = Account_ID
    data = {"data": [contact_data]}
    response = requests.post(url, headers=headers, json=data)
    try:
        
        if response.status_code in [200,201]:
            data = response.json()
            contact_id = response.json()["data"][0]["details"]["id"]
            # link_contact_to_company_id(access_token, Account_ID, contact_id)
        else:
            logger.warning(f"Failed to add contact. Status code: {response.json()}")
            contact_id = ''

        return contact_id

    except requests.exceptions.RequestException as e:
        logger.error(f"Error adding contact: {e}")
        return ''




def update_contact(access_token,payload):
    url = f"https://www.zohoapis.ca/crm/v2/Contacts"
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }
    response = requests.put(url, headers=headers, json=payload)

    return response.json()

