import requests
from utils.helpers import *

logger = get_logger(__name__)

## Add Companies registered through the bubble App
def add_bubble_companies(access_token,company_data):
    url = "https://www.zohoapis.ca/crm/v2/Accounts"
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }

    cleaned_company_data = {}
    for key,value in company_data.items():
        if value is not None:
            cleaned_company_data[key]=value

    payload = {"data": [cleaned_company_data]}
    
    response = requests.post(url, headers=headers, json=payload)
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

def add_bubble_contact(access_token,contact_data,Account_ID):
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
            link_contact_to_company_id(access_token, Account_ID, contact_id)
        else:
            print(f"Failed to add contact. Status code: {response.status_code}")

        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Error adding contact: {e}")
        return None




def update_contact(access_token,payload):
    url = f"https://www.zohoapis.ca/crm/v2/Contacts"
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }
    response = requests.put(url, headers=headers, json=payload)

    return response.json()





def add_carrier(access_token :str, carriers : dict):


    url = "https://www.zohoapis.ca/crm/v2/Carriers"

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, json=carriers)

    return response