import requests
from utils.helpers import *

logger = get_logger(__name__)

MODULE_URL = "https://www.zohoapis.ca/crm/v2/Deals"

VEHICLE_MODULE_URL = "https://www.zohoapis.ca/crm/v2/Vehicles"

def attach_release_form(token : str,  zoho_job_id : str, attachment_urls : list) -> dict:
    # Prepare the headers

    attachment_url = f"{MODULE_URL}/{zoho_job_id}/Attachments"
    headers = {
        "Authorization": f"Zoho-oauthtoken {token}"
    }
    resp = []
    for release_form in attachment_urls:
        data = {
            "attachmentUrl": release_form
        }
        
        response = requests.post(attachment_url, headers=headers, data=data)
        
        if response.status_code == 200:
            logger.info(f"Successfully attached release form to Job: {zoho_job_id}")
        else:
            logger.error(f"Failed to attach release form to Job for {response.json()}")

        resp.append(response.json())

    return resp

def add_order(order_data : dict, token : str, release_form : list, vehicles : list) -> dict:
    try:

        order_data['Layout'] =  {
                "name":"Transport Job",
                "id": "3384000001562002"
            }
        
        payload = {"data": [order_data]}

        response = requests.post(MODULE_URL, headers=get_header(token), json=payload)
        logger.info(response.json())
        logger.info(f"Order creation response : {response}")

        try:
            if response.status_code == 201:
                order_id =  response.json()["data"][0]["details"]["id"]
                logger.info(f"Successfully added Order Job : {order_id}")
                ## add the vehicles
                vehicle_response = add_vehicles(token,vehicles, order_id,order_data['PickupLocation'],order_data['Drop_off_Location'])
                try:
                        
                    document_response = attach_release_form(token, order_id, release_form)
                    logger.info(f"Document Attachment response : {document_response}")
                except Exception as e:
                    logger.warning(f"Document Attachment error : {e}")
                
            else:
                logger.error(f"Failed to add Order for {response.json()}")

            return {
                "status":"sucess",
                "code":201,
                "order_id":order_id,
                "vehicles":vehicle_response
            }
        
        except Exception as e:
            logger.error(f"Error Creating Order Request: {e}")

        return response.json()
    except Exception as e:
        logger.error(f"Error Creating Order: {e}")

        return {"message": "Error Creating Order","error": str(e)}

def add_vehicles(token :str , vehicles : list, Order_ID : str,pickuplocation : str, dropofflocation:str):
    
    data = {
        "data":vehicles
    }

    for i in range(len(vehicles)):
        vehicles[i]['Layout'] =  {
        "name":"Transport Vehicles",
        "id": "3384000001943151"
    }
        vehicles[i]['Name'] = vehicles[i]['Make'] + " " + vehicles[i]['Model'] + " " + vehicles[i]['Trim'] + " - "+ vehicles[i]['VIN']
        vehicles[i]['Source'] = "Transport Request"
        vehicles[i]['Order_Status'] = "Pending"
        vehicles[i]['Deal_ID'] = Order_ID
        vehicles[i]['Pickup_Location'] = pickuplocation
        vehicles[i]['Dropoff_Location'] = dropofflocation



    batch_response = requests.post(VEHICLE_MODULE_URL,json=data,headers=get_header(token))

    logger.info(f"vehicle batch response {batch_response}")

    for i,response in enumerate(batch_response.json()['data']):
        vehicles[i]['Vehicle_ID'] = response['details']['id']

    logger.info(f"vehicle added response {batch_response.json()}")

    return vehicles

def update_order(updated_data : dict, token : str) -> dict:

    headers = {
        "Authorization": f"Zoho-oauthtoken {token}",
        "Content-Type": "application/json",
    }

    job_id = updated_data['id'] 
    try:
        if not job_id:
            logger.info(f"Order ID not found")

            return {"message": "order ID not found in request body"}
        else:
            payload = {"data": [updated_data]}
            response = requests.patch(MODULE_URL, headers=headers, json=payload)

            if response.status_code == 200:
                logger.info(f"Successfully updated Order Job : {job_id}")
            
            else:
                logger.error(f"Failed to update Order for {response.json()}")

            return response.json()
        
    except Exception as e:
        logger.error(f"Error Updating Order: {e}")

        return {"message": "Error Updating Order","error": str(e)}