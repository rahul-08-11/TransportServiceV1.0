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
            orders_list = body.get("Orders",[{}])

            for i, order in enumerate(orders_list):
                Id =f"#{order_id + i}" 
                try:
                    release_forms = order.get("release_form","")
                    logger.info(f"release_form : {release_forms}")
                except Exception as e:
                    logger.error(f"Func Main  Error: {e}")

                # format deal name 
                customer_name = body.get("Customer_name","")

                OrderObj = Order(
                    Deal_Name=f"{customer_name} - {Id}",
                    Customer_id = body.get("Customer_id",""),
                    Customer_Name =customer_name,
                    Dropoff_Location = order.get("Dropoff_Location",""),
                    OrderID = Id,
                    Pickup_Location = order.get("Pickup_Location",""),
                    Vehicle_Details = order.get("Vehicle_Details",[{}]),
                    Customer_Notes = order.get("Customer_Notes","")
                )

                token = token_instance.get_access_token()
                response = TJApi.add_order(dict(OrderObj), token, release_forms)

                try:
                    job_id = response["data"][0]["details"]["id"]

                    dbobj = OrdersDB(
                        OrderID=Id,  # Set the OrderID
                        TransportRequestID=job_id,  # Add a comma here
                        CustomerID=OrderObj.Customer_id,
                        CustomerName=OrderObj.Customer_Name,
                        Status="Pending",
                        PickupLocation=OrderObj.Pickup_Location,
                        DropoffLocation=OrderObj.Dropoff_Location,

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
                    

                    await update_order({"id": Zoho_Job_ID, "Name": order_id})

                    try:
                        customer_body = body.get("Customer","")
                        customer_id = customer_body['id']
                        customer_name = customer_body['name']
                    except Exception as e:
                        customer_name = 'n/a'
                        customer_id = 'n/a'
                        logger.error(f"Func Main  Error: {e}")

                    dbobj = OrdersDB(
                        OrderID=order_id,  # Set the OrderID
                        TransportRequestID=Zoho_Job_ID,  # Add a comma here
                        CustomerID=customer_id,
                        CustomerName=customer_name
                    )
                    session.add(dbobj)
                    session.commit()
                    logger.info("commited successfully")
            except Exception as e:
                logger.error(f"Func Main  Error: {e}")
                
            
            pickup_location = body.get('pickuploc', 'n/a')
            dropoff_location = body.get('dropoffloc', 'n/a')
            recommendation_df = recommend_carriers(carrierT, pickup_location, dropoff_location)
            
            response = CleadApi.add_leads(recommendation_df,Zoho_Job_ID, token,session)
            
            return response
        
    except Exception as e:
        logger.error(f"Func Main  Error: {e}")
        return {
            "error": str(e)
        }
    


async def quotes_operation(body : dict) -> func.HttpResponse:
    """ Handle quotes operations"""
    
    try:
# 
        with DatabaseConnection(connection_string=os.getenv("SQL_CONN_STR")) as session:
            logger.info(f"DB Connection established")
            try:
                quote = TransportQuotation(
                    TransportRequestID=body.get("TransportRequestID","-"),
                    CarrierName=body.get("CarrierName","-"),
                    DropoffLocation=body.get("DropoffLocation","-"), 
                    PickupLocation=body.get("PickupLocation","-"),
                    EstimatedPickupTime=body.get("EstimatedPickupTime","-"),
                    EstimatedDropoffTime=body.get("EstimatedDropoffTime","-"),
                    Estimated_Amount=body.get("Estimated_Amount","-")
                )
                session.add(quote)
                session.commit()
            except Exception as e:
                logger.error(f"Func Main  Error: {e}")

    except Exception as e:
        logger.error(f"Func Main  Error: {e}")