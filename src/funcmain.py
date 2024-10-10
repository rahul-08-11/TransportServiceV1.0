from src.apis import *
from models import *
from utils.helpers import *
import azure.functions as func
import json

logger = get_logger(__name__)

global token_instance
token_instance = TokenManager()


async def create_order(body: json) -> dict:
    """ Create an Order in the CRM"""

    try:

        OrderObj = Order(
            Customer_id = body.get("Customer_id",""),
            Customer_Name = body.get("Customer_Name",""),
            Actual_Dropoff_Time = body.get("Actual_Dropoff_Time",""),
            Actual_Pickup_Time = body.get("Actual_Pickup_Time",""),
            Dropoff_Location = body.get("Dropoff_Location",""),
            Email = body.get("Email",""),
            Job_Price = body.get("Job_Price",""),
            Order_ID = body.get("Order_ID",""),
            Make = body.get("Make",""),
            Model = body.get("Model",""),
            Payment_Status = body.get("Payment_Status",""),
            Pickup_Location = body.get("Pickup_Location",""),
            Scheduled_Dropoff_Time = body.get("Scheduled_Dropoff_Time",""),
            Scheduled_Pickup_Time = body.get("Scheduled_Pickup_Time",""),
            Shipment_Status = body.get("Shipment_Status",""),
            Name = body.get("Name",""),
            Trim = body.get("Trim",""),
            Vin = body.get("Vin",""),
            Year = body.get("Year",""),
        )

        token = token_instance.get_access_token()
        response = TJApi.add_order(dict(OrderObj), token)
        logger.info(f"Response Received : {response}")

        return response
    
    except Exception as e:
        logger.error(f"Func Main  Error: {e}")
        return {
            "error": str(e)
        }

async def update_order(body: json) -> dict:
    """ Update an Order in the CRM"""

    try:
        token = token_instance.get_access_token()

        response = TJApi.update_order(body, token)

        return response
    

    except Exception as e:
        logger.error(f"Func Main  Error: {e}")
        return {
            "error": str(e)
        }