import requests
from utils.helpers import *

logger = get_logger(__name__)

MODULE_URL = "https://www.zohoapis.ca/crm/v2/Transport_Job"

def attach_release_form(token : str,  zoho_job_id : str, release_forms : list) -> dict:
    # Prepare the headers
    headers = {
        "Authorization": f"Zoho-oauthtoken {token}"
    }

    # Prepare the data for the attachment
    data = {
        "attachmentUrl": release_forms
    }

    attachment_url = f"{MODULE_URL}/{zoho_job_id}/Attachments"

    response = requests.post(attachment_url, headers=headers, data=data)

    if response.status_code == 200:
        logger.info(f"Successfully attached release form to Job : {zoho_job_id}")
        return response.json()
    else:
        logger.error(f"Failed to attach release form to Job for {response.json()}")
        return response.json()



def get_zoho_id(access_token :str, unique_identifier : str, field_name :str , module_name : str):
    """
    unique_identifier : Primary key to search
    field_name : Name of the field to be searched

    """
    # API endpoint
    url = "https://www.zohoapis.ca/crm/v2/{module_name}/search"

    params = {"criteria": f"{field_name}:equals:{unique_identifier}"}

    # Authorization Header
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
    }

    # Make GET request to fetch id
    response = requests.get(url, params=params, headers=headers)

    logger.info(f"response received : {response}")
    # Check if request was successful
    if response.status_code == 200:
        data = response.json()
        if data["data"]:
            id = data["data"][0]["id"]
            return id
        else:
            return None
    else:
        return None


def add_order(order_data : dict, token : str, release_forms : list) -> dict:

    try:

        headers = {
            "Authorization": f"Zoho-oauthtoken {token}",
            "Content-Type": "application/json",
        }

        # customer_id = order_data['Customer_id']

        try:
            pass
            # if not customer_id:
            #     logger.info(f"Customer ID not found : Searching by CustomerName : {order_data['Customer_Name']}")
            #     customer_id = get_zoho_id(access_token=token, unique_identifier=order_data['Customer_Name'], field_name="Account_Name",module_name="Accoutns")
               
            #     if customer_id:
            #         logger.info(f"Customer ID found : {customer_id}")
            #         order_data['Customer_id'] = customer_id


        except Exception as e:
            logger.warning(f"Customer ID or Searched Name not found: {e}")

        payload = {"data": [order_data]}

        response = requests.post(MODULE_URL, headers=headers, json=payload)

        logger.info(f"Order creation response : {response}")

        try:
            if response.status_code == 201:
                order_id =  response.json()["data"][0]["details"]["id"]
                logger.info(f"Successfully added Order Job : {order_id}")
                document_response = attach_release_form(token, order_id, release_forms)
                logger.info(f"Document Attachment response : {document_response}")
                
            else:
                logger.error(f"Failed to add Order for {response.json()}")

            return response.json()
        
        except Exception as e:
            logger.error(f"Error Creating Order Request: {e}")

        return response.json()
    except Exception as e:
        logger.error(f"Error Creating Order: {e}")

        return {"message": "Error Creating Order","error": str(e)}



def update_order(updated_data : dict, token : str) -> dict:

    headers = {
        "Authorization": f"Zoho-oauthtoken {token}",
        "Content-Type": "application/json",
    }

    order_id = updated_data['id'] 
    try:
        if not order_id:
            logger.info(f"Order ID not found")

            return {"message": "order ID not found in request body"}
        else:
            payload = {"data": [updated_data]}
            response = requests.patch(MODULE_URL, headers=headers, json=payload)

            if response.status_code == 200:
                logger.info(f"Successfully updated Order Job : {order_id}")
            
            else:
                logger.error(f"Failed to update Order for {response.json()}")

            return response.json()
        
    except Exception as e:
        logger.error(f"Error Updating Order: {e}")

        return {"message": "Error Updating Order","error": str(e)}

    

    