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
                release_form = body.get("release_form","")
                release_form = manage_prv(release_form)
                logger.info(f"release_form : {release_form}")
            except Exception as e:
                logger.error(f"Func Main  Error: {e}")

            # format deal name 
            customer_name = body.get("Customer_name","")
            
            OrderObj = Order(
                Deal_Name=order_id,
                Customer_id = body.get("Customer_id",""),
                Customer_Name =customer_name,
                Dropoff_Location = body.get("Dropoff_Location",""),
                Pickup_Location = body.get("Pickup_Location",""),
                Customer_Notes = body.get("Customer_Notes",""),
                Vehicle_Subform = body.get("Orders")
            )

            token = token_instance.get_access_token()
            print(dict(OrderObj))
            response = TJApi.add_order(dict(OrderObj), token, release_form)

            try:
                job_id = response["data"][0]["details"]["id"]

                dbobj = OrdersDB(
                    OrderID=order_id,  # Set the OrderID
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


async def register_account(req : func.HttpRequest):
    """ Register new account """
    try:
        # Get the access token
        access_token=token_instance.get_access_token()

        # Get the form data
        body = req.form
        logging.info(f"received form data: {body}")

        # Create a Company Instance
        company = Company(
            Account_Name=body.get('Account_Name'),
            Dealer_License_Number=body.get('Dealer_License_Number'),
            Dealer_Phone=body.get('Dealer_Phone'),
            Category=body.get('Dealership_Type'),
            Address=body.get('Address'),
            ExpiryDate=body.get('ExpiryDate'),
            Business_Number=body.get('Business_Number'),
            CRA_HST_GST_Number=body.get('CRA_HST_GST_Number'),
            SK_PST_Number=body.get('SK_PST_Number'),
            Email=body.get('Company_Email'),
            BC_PST_Number=body.get('BC_PST_Number'),
            Website = body.get('Website','')

        )

        # Add Company
        response = add_bubble_companies(access_token,dict(company))

        if response.status_code == 201:
            logging.info(f"Add Customer :  {response.json()}")
            return func.HttpResponse(response, status_code=201)

        else:
            return func.HttpResponse(response, status_code=500)


    except Exception as e:
        logging.error(f"Error adding submitted company in zoho {e}")
        return func.HttpResponse(json.dumps({"error":str(e)}), status_code=500)
    
    


# async def register_carriers(req : func.HttpRequest):
#     """ Register new Carriers """
#     try:
#         # Get the access token
