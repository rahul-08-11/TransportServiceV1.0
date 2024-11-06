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
                release_forms_raw = body.get("release_form","")
                release_forms_items = release_forms_raw.split(",")
                release_forms = list(map(manage_prv, release_forms_items))

                logger.info(f"release_form : {release_forms}")
            except Exception as e:
                release_forms = list()
                logger.error(f"Func Main  Error: {e}")

            # format deal name 
            customer_name = body.get("Customer_name","")
            
            OrderObj = Order(
                Deal_Name=order_id,
                Customer_id = body.get("Customer_id",""),
                Customer_Name =customer_name,
                Drop_off_Location = body.get("Dropoff_Location",""),
                PickupLocation = body.get("Pickup_Location",""),
                Customer_Notes = body.get("Customer_Notes",""),
                Vehicle_Subform = body.get("Orders")
            )

            token = token_instance.get_access_token()
            print(dict(OrderObj))
            response = TJApi.add_order(dict(OrderObj), token, release_forms)

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


async def register_account(req : func.HttpRequest):
    """ Register new account """
    try:

        # Get the access token
        access_token=token_instance.get_access_token()

        # Get the json data
        body = req.get_json()
        logging.info(f"received form data: {body}")

        # Create a Company Instance
        company = Company(
            Account_Name=body.get('Account_Name'),
            Dealer_License_Number=body.get('Dealer_License_Number'),
            Category=body.get('Dealership_Type'),
            Address=body.get('Address'),
            ExpiryDate=body.get('ExpiryDate'),
            Business_Number=body.get('Business_Number'),
            CRA_HST_GST_Number=body.get('CRA_HST_GST_Number'),
            SK_PST_Number=body.get('SK_PST_Number'),
            Email=body.get("PrimaryContact").get("Email"),
            Dealer_Phone=body.get("PrimaryContact").get("Phone"),
            BC_PST_Number=body.get('BC_PST_Number'),
            Website = body.get('Website','')

        )

        # Add Company
        response = add_bubble_Customer(access_token,dict(company))
        logger.info(response)

        if response.status_code == 201:
            ## means account register sucessfully

            customer_id = response.json()["data"][0]["details"]["id"]
            try:
             
                logger.info("Adding Primary Contact")
                primaryID = add_customer_contact(access_token,body.get("PrimaryContact"),customer_id)
            except Exception as e:
                logger.error(f"Error Adding Primary Contact: {e}")
                primaryID = ''

            try:
     
                logger.info("Adding Secondary Contact")
                secondaryID = add_customer_contact(access_token,body.get("OptionalContact"),customer_id)
            except Exception as e:
                logger.error(f"Error Adding Secondary Contact: {e}")
                secondaryID = ''

            resp = {
                "status":"success",
                "message":"Account created successfully",
                "code":201,
                "CustomerID":customer_id,
                "PrimaryContactID":primaryID,
                "OptionalContactID":secondaryID
            }
        elif response.status_code == 202:
            resp = {
                "status":"Duplicate Error",
                "message":"Duplicate Account found",
                "code":202
            }

        else:
            resp = {
             "status":response.status_code,
             "message":response.text,   
            }
    

        return resp


    except Exception as e:
        logging.error(f"Error adding submitted company in zoho {e}")
        return func.HttpResponse(json.dumps({"error":str(e)}), status_code=500)
    
    


async def register_carriers(req : func.HttpRequest):
    """ Register new Carriers """
    try:
        # Get the access token
        access_token=token_instance.get_access_token()

        # Get the json data
        body = req.get_json()

        carrierObj = Carrier(
            Name=body.get('CarrierName'),
            Carrier_Type=body.get('Carrier_Type'),
            OperatingRegions=body.get('OperatingRegions'),
            Transport_Type = body.get('Transport_Type'),
            Phone_Number = body.get("PrimaryContact").get("Phone"),
            Email = body.get("PrimaryContact").get("Email"),
            Address = body.get('Address')
        )


        response = add_bubble_carrier(access_token,dict(carrierObj))
        logger.info(response.json())


        if response.status_code == 201:
            carrier_id = response.json()["data"][0]["details"]["id"]

            try:
                logger.info("Adding Primary Contact")
                payload = body.get("PrimaryContact")
                payload['Carrier']=carrier_id
                primaryID = add_carrier_contact(access_token,payload)
            except Exception as e:
                logger.error(f"Error Adding Contact: {e}")
                primaryID = ''

            try:
        
                logger.info("Adding Secondary Contact")
                payload = body.get("OptionalContact")
                payload['Carrier']=carrier_id
                secondaryID = add_carrier_contact(access_token,body.get("OptionalContact"))
            except Exception as e:
                logger.error(f"Error Adding Contact: {e}")
                secondaryID = ''

            resp = {
                "status":"success",
                "message":"Carrier created successfully",
                "code":201,
                "CarrierID":carrier_id,
                "PrimaryContactID":primaryID,
                "OptionalContactID":secondaryID
            }

        elif response.status_code == 202:
            resp = {
                "status":"Duplicate Error",
                "message":"Duplicate Carrier found",
                "code":202
            }
        else:
            resp = {
             "status":response.status_code,
             "message":response.text,   
            }
    

        return resp


    except Exception as e:
        logging.error(f"Error adding submitted Carrier in zoho {e}")



