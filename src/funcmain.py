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
        order_id = f"#{order_id}"
        try:
            try:
                Vehicle_Subform = body.get("Vehicles","")

                vehicles = [{ k: v for k, v in vehicle.items() if v != "ReleaseForm"} for vehicle in Vehicle_Subform]

                absrelease_forms = [vehicle["ReleaseForm"] for vehicle in Vehicle_Subform if vehicle['ReleaseForm'] not in ['null',None,'']]

                if absrelease_forms:
                    release_forms = list(map(manage_prv, absrelease_forms))

                else:
                    release_forms = list()
                logger.info(f"Release Forms : {release_forms}")

            except Exception as e:
                release_forms = list()
                logger.error(f"Func Main  Error: {e}")

            # format deal name 
            customer_name = body.get("Customer_name","")
            
            OrderObj = OrderApi(
                Deal_Name=order_id,
                Customer_id = body.get("Customer_id",""),
                Customer_Name =customer_name,
                Drop_off_Location = body.get("Dropoff_Location",""),
                PickupLocation = body.get("Pickup_Location",""),
                Customer_Notes = body.get("Customer_Notes",""),
                Vehicle_Subform = vehicles,
            )

            token = token_instance.get_access_token()
            print(dict(OrderObj))
            response = OrderApi.add_order(dict(OrderObj), token, release_forms,Vehicle_Subform)

            try:
                job_id = response["data"][0]["details"]["id"]

                dbobj = OrdersDB(
                    OrderID=order_id,  # Set the OrderID
                    TransportRequestID=job_id,  # Add a comma here
                    CustomerID=OrderObj.Customer_id,
                    CustomerName=OrderObj.Customer_Name,
                    Status="Pending",
                    PickupLocation=OrderObj.PickupLocation,
                    DropoffLocation=OrderObj.Drop_off_Location,

                )
                session.add(dbobj)
                session.commit()
                slack_msg = f"""
                🚚 *New Transport Request :* 

                    Details: 
                    - Order ID: `{order_id}`  
                    - Transport Volume: `{len(Vehicle_Subform)}` vehicles  
                    - Pickup Location: {OrderObj.PickupLocation}  
                    - Drop-off Location: {OrderObj.Drop_off_Location}
                    [View Order Details](https://crm.zohocloud.ca/crm/org110000402423/tab/Potentials/{order_id})  
                """
        
            except Exception as e:
                logger.error(f"Func Main  Error: {e}")
                    
            logger.info(f"Response Received : {response}")

            return {
                "status":"success",
                "orderID":order_id,
                "zoho_order_id":job_id
            }
        
        except Exception as e:
            logger.error(f"Func Main  Error: {e}")
            return {
                "error": str(e)
            }

async def update_order(body: json) -> dict:
    """ Update an Order in the CRM"""

    try:
        token = token_instance.get_access_token()

        response = OrderApi.update_order(body, token)

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
                if not order_id.startswith("#"):
                    order_id = f"#{get_order_id(session)}"
                    customer_body = body.get("Customer","")

                    try:
                        customer_body = body.get("Customer","")
                        customer_id = customer_body['id']
                        customer_name = customer_body['name']
                    except Exception as e:
                        customer_name = 'n/a'
                        customer_id = 'n/a'
                        logger.error(f"Func Main  Error: {e}")

                    await update_order({"id": Zoho_Job_ID, "Deal_Name": order_id})

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