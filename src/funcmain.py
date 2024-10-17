from src.apis import *
from utils.helpers import *
from utils.model import *
import azure.functions as func
from recomendation import recommend_carriers
import json
import pandas as pd
import os
# # # Load Env Variables
# from dotenv import load_dotenv
# load_dotenv()

logger = get_logger(__name__)

global token_instance
token_instance = TokenManager()


async def create_order(body: json) -> dict:
    """ Create an Order in the CRM"""
    with DatabaseConnection(connection_string=os.getenv("SQL_CONN_STR")) as session:
        # Create the order ID for new request
        order_id = get_order_id(session)

        try:

            try:
                release_forms = body.get("release_form","")
                logger.info(f"release_form : {release_forms}")
            except Exception as e:
                logger.error(f"Func Main  Error: {e}")

            OrderObj = Order(
                Name=order_id,
                Customer_id = body.get("Customer_id",""),
                Customer_Name = body.get("Customer_Name",""),
                Dropoff_Location = body.get("Dropoff_Location",""),
                Order_ID = body.get("Order_ID",""),
                Pickup_Location = body.get("Pickup_Location",""),
                Vehicle_Details = body.get("Vehicle_Details",[{}]),
                Customer_Notes = body.get("Customer_Notes","")
            )

            token = token_instance.get_access_token()
            response = TJApi.add_order(dict(OrderObj), token, release_forms)

            try:
                id = response["data"][0]["details"]["id"]

                dbobj = OrdersDB(
                    OrderID=order_id,  # Set the OrderID
                    TransportRequestID=id,  # Add a comma here
                    CustomerID=OrderObj.Customer_id,
                    CustomerName=OrderObj.Customer_Name
                )
                session.add(dbobj)
                session.commit()

            except Exception as e:
                logger.error(f"Func Main  Error: {e}")
                
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
    

async def create_potential_carrier(body , carrierT: pd.DataFrame) -> dict:
    """ Create an Potential Carrier in the CRM"""
    try:
        token = token_instance.get_access_token()
        Zoho_Job_ID=body.get("Zoho_Job_ID","")
        order_id = body.get("order_id","-")
        logger.info(f"Adding Potential Carriers for {Zoho_Job_ID}")

        collective_response = {}
        with DatabaseConnection(connection_string=os.getenv("SQL_CONN_STR")) as session:
            logger.info(f"DB Connection established")
            try:
                # check if order entered directly through Zoho
                if order_id == "-":
                    order_id = get_order_id(session)
                    customer_body = body.get("Customer","")
                    

                    update_order({"id": order_id})
                    dbobj = OrdersDB(
                        OrderID=order_id,  # Set the OrderID
                        TransportRequestID=id,  # Add a comma here
                        CustomerID=customer_body['id'],
                        CustomerName=customer_body['Name']
                    )
                    session.add(dbobj)
                    session.commit()
            except Exception as e:
                logger.error(f"Func Main  Error: {e}")
                
            for i, vehicle in enumerate(body['Vehicle_Details']):
                logger.info(vehicle)
                pickup_location = body.get('pickuploc', 'n/a')
                dropoff_location = body.get('dropoffloc', 'n/a')
                recommendation_df = recommend_carriers(carrierT, pickup_location, dropoff_location)
               
                response = CleadApi.add_leads(recommendation_df,Zoho_Job_ID, token,session)
                
                collective_response[f"Vehicle {i+1}"] = response
            return collective_response
        
    except Exception as e:
        logger.error(f"Func Main  Error: {e}")
        return {
            "error": str(e)
        }