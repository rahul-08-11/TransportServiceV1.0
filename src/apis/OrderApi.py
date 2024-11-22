import requests
from utils.helpers import *
import asyncio
import aiohttp


logger = get_logger(__name__)

MODULE_URL = "https://www.zohoapis.ca/crm/v2/Deals"

VEHICLE_MODULE_URL = "https://www.zohoapis.ca/crm/v2/Vehicles"


async def attach_release_form_async(token: str, zoho_id: str, attachment_urls: list, module: str):
    """Attach release forms asynchronously."""
    if module == "Deals":
        attachment_url = f"{MODULE_URL}/{zoho_id}/Attachments"
    elif module == "Vehicles":
        attachment_url = f"{VEHICLE_MODULE_URL}/{zoho_id}/Attachments"

    headers = {"Authorization": f"Zoho-oauthtoken {token}"}

    async with aiohttp.ClientSession() as session:
        tasks = []
        for release_form in attachment_urls:
            data = {"attachmentUrl": release_form}
            tasks.append(send_attachment_request(session, attachment_url, headers, data))

        responses = await asyncio.gather(*tasks, return_exceptions=True)
        for response in responses:
            if isinstance(response, Exception):
                logger.error(f"Attachment request failed: {response}")
            else:
                logger.info(f"Attachment response: {response}")


async def send_attachment_request(session, url, headers, data):
    """Send an individual attachment request."""
    async with session.post(url, headers=headers, data=data) as response:
        if response.status == 200:
            return await response.json()
        else:
            raise Exception(f"Failed to attach file: {await response.text()}")
        
def add_order(order_data : dict, token : str, release_form_lis : list, vehicles : list) -> dict:
    try:

        order_data['Layout'] =  {
                "name":"Transport Job",
                "id": "3384000001562002"
            }
        
        payload = {"data": [order_data]}

        zoho_response = requests.post(MODULE_URL, headers=get_header(token), json=payload)
        logger.info(f"Zoho Order creation response : {zoho_response.json()}")

        try:
            if zoho_response.status_code == 201:
                order_id =  zoho_response.json()["data"][0]["details"]["id"]
                logger.info(f"Successfully added Order Job : {order_id}")
                ## add the vehicles
                vehicle_response,tasks = add_vehicles(token,vehicles, order_id,order_data['PickupLocation'],order_data['Drop_off_Location'])
                try:
        
                    tasks.append(attach_release_form_async(token, order_id, release_form_lis, module="Deals"))
                    # loop = asyncio.get_event_loop()
                    for task in tasks:
                        asyncio.create_task(task)
            
                    # logger.info(f"Document Attachment response : {loop}")
                except Exception as e:
                    logger.warning(f"Document Attachment error : {e}")
                
            else:
                logger.error(f"Failed to add Order for {vehicle_response.json()}")

            return {
                "status":"sucess",
                "code":201,
                "Deal_Name":order_data['Deal_Name'],
                "zoho_order_id":order_id,
                "vehicles":vehicle_response
            }
        
        except Exception as e:
            logger.error(f"Error Creating Order Request: {e}")

        return vehicle_response.json()
    except Exception as e:
        logger.error(f"Error Creating Order: {e}")

        return {"message": "Error Creating Order","error": str(e)}

def add_vehicles(token :str , vehicles : list, Order_ID : str,pickuplocation : str, dropofflocation:str):
    """ Add vehicles to the order """
    data = {
        "data":vehicles
    }
    layout_info = {
        "name": "Transport Vehicles",
        "id": "3384000001943151"
    }

    for vehicle in vehicles:
        vehicle.update({
            "Layout": layout_info,
            "Name": f"{vehicle['Make']} {vehicle['Model']} {vehicle['Trim']} - {vehicle['VIN']}",
            "Source": "Transport Request",
            "Order_Status": "Pending",
            "Deal_ID": Order_ID,
            "Pickup_Location": pickuplocation,
            "Dropoff_Location": dropofflocation
        })


    batch_vehicle_resp = requests.post(VEHICLE_MODULE_URL,json=data,headers=get_header(token))

    logger.info(f"vehicle batch response {batch_vehicle_resp}")

    loop = asyncio.get_event_loop()
    tasks = []
    for i, response in enumerate(batch_vehicle_resp.json()["data"]):
        vehicles[i]["Vehicle_ID"] = response["details"]["id"]
        del vehicles[i]["Layout"]
        del vehicles[i]["Source"]

        parsed_url = manage_prv(vehicles[i]["ReleaseForm"])

        # Attach release form asynchronously
        task = attach_release_form_async(
            token, vehicles[i]["Vehicle_ID"], [parsed_url], "Vehicles"
        )
        tasks.append(task)

    return vehicles,tasks

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