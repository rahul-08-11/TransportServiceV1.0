import requests
from utils.helpers import *
import asyncio
import aiohttp
import os

logger = get_logger(__name__)

MODULE_URL = "https://www.zohoapis.ca/crm/v2/Deals"

VEHICLE_MODULE_URL = "https://www.zohoapis.ca/crm/v2/Vehicles"
TEMP_DIR = "/tmp"

def attach_release_form(token: str, zoho_id: str, attachment_urls: list, module: str):
    """Attach release forms synchronously."""
    if module == "Deals":
        attachment_url = f"{MODULE_URL}/{zoho_id}/Attachments"
    elif module == "Vehicles":
        attachment_url = f"{VEHICLE_MODULE_URL}/{zoho_id}/Attachments"
    else:
        raise ValueError("Invalid module specified")

    headers = {"Authorization": f"Zoho-oauthtoken {token}"}

    for release_form in attachment_urls:
        file_name = os.path.basename(release_form)
        local_file_path = os.path.join(TEMP_DIR, file_name)

        # Download the file if it doesn't exist
        if not os.path.exists(local_file_path):
            download_file(release_form, local_file_path)

        with open(local_file_path, "rb") as file:
            files = {
                "file": (file_name, file, "application/octet-stream")
            }
            response = requests.post(attachment_url, headers=headers, files=files)
            if response.status_code == 200:
                logger.info(f"File {file_name} attached successfully to {module} {zoho_id}")
            else:
                logger.error(f"Failed to attach file {file_name}: {response.text}")

        # Clean up local file
        if os.path.exists(local_file_path) and module=="Deals":
            os.remove(local_file_path)

def download_file(url: str, destination_path: str):
    """Download a file synchronously from a public URL."""
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(destination_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        logger.info(f"Downloaded file to: {destination_path}")
    else:
        raise Exception(f"Failed to download file from {url}: {response.status_code}")

def add_order(order_data: dict, token: str, release_form_list: list, vehicles: list) -> dict:
    """Add a transport order and attach release forms synchronously."""
    try:
        order_data['Layout'] = {
            "name": "Transport Job",
            "id": "3384000001562002"
        }

        payload = {"data": [order_data]}
        zoho_response = requests.post(MODULE_URL, headers=get_header(token), json=payload)
        logger.info(f"Zoho Order creation response: {zoho_response.json()}")

        if zoho_response.status_code == 201:
            order_id = zoho_response.json()["data"][0]["details"]["id"]
            logger.info(f"Successfully added Order Job: {order_id}")

            # Add vehicles
            vehicle_response = add_vehicles(token, vehicles, order_id, order_data['PickupLocation'], order_data['Drop_off_Location'])

            # Attach release forms
            attach_release_form(token, order_id, release_form_list, module="Deals")

            return {
                "status": "success",
                "code": 201,
                "Deal_Name": order_data['Deal_Name'],
                "zoho_order_id": order_id,
                "vehicles": vehicle_response
            }
        else:
            logger.error(f"Failed to add Order. Response: {zoho_response.json()}")
            return {"status": "failure", "code": zoho_response.status_code}

    except Exception as e:
        logger.error(f"Error Creating Order: {e}")
        return {"message": "Error Creating Order", "error": str(e)}

def add_vehicles(token: str, vehicles: list, order_id: str, pickup_location: str, dropoff_location: str):
    """Add vehicles to the order."""
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
            "Deal_ID": order_id,
            "Pickup_Location": pickup_location,
            "Dropoff_Location": dropoff_location
        })

    data = {"data": vehicles}
    response = requests.post(VEHICLE_MODULE_URL, json=data, headers=get_header(token))
    logger.info(f"Vehicle batch response: {response.json()}")

    for i, resp in enumerate(response.json()["data"]):
        vehicles[i]["Vehicle_ID"] = resp["details"]["id"]
        attach_release_form(token, resp["details"]["id"], vehicles[i]["ReleaseForm"], module="Vehicles")
        del vehicles[i]["Layout"]
        del vehicles[i]["Source"]

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