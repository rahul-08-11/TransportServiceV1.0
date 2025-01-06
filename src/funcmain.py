from src.apis import *
from utils.helpers import *
from utils.model import *
import azure.functions as func
from recomendation import recommend_carriers
import json
import pandas as pd
import os
from src.dbConnector import *
from sqlalchemy import and_ ,func as sqlfunc
from sqlalchemy.exc import IntegrityError
# # # Load Env Variables
from dotenv import load_dotenv
load_dotenv()

logger = get_logger(__name__)

global token_instance
token_instance = TokenManager()


class TransportOrders:
    def __init__(self) -> None:
        """
        Initialize the TransportOrders class."""

    def __repr__(self) -> str:
        return str(self.body)
    

    def parse_request(self,body):
        ## prase release form
        try:

            absrelease_forms = [vehicle["ReleaseForm"] for vehicle in body.get("Vehicles","") if vehicle['ReleaseForm'] not in ['null',None,'']]

            if absrelease_forms:
                ## create list of release form urls
                release_forms = list(map(manage_prv, absrelease_forms)) 

            else:
                ## assign empty list
                release_forms = list()
            logger.info(f"Release Forms : {release_forms}")

        except Exception as e:
            release_forms = list()
            logger.error(f"Func Main  Error: {e}")

        return release_forms
    
    def _create_order_id(self,session) -> int:
        # Query to fetch the maximum OrderID
        last_order = session.query(sqlfunc.max(OrdersDB.OrderID)).scalar()
        last_id = last_order if last_order is not None else None
        try:
            result = int(last_id.replace("#",""))
            logger.info(result)
        except Exception as e:
            result = None

        sorder_id = 10001

        if result == None:
            order_id = sorder_id
        else:
            order_id = 1 + result

        return order_id
            
    

    async def _create_order(self, body:json) -> dict:
        try:
            
            token = token_instance.get_access_token()
            release_forms = self.parse_request(body)

            with DatabaseConnection(connection_string=os.getenv("SQL_CONN_STR")) as session:
                # fetch the order ID for new request
                order_id = self._create_order_id(session)
                order_id = f"#{order_id}"
                OrderObj = Order(
                    Deal_Name=order_id,
                    Customer_id = body.get("Customer_id",""),
                    Customer_Name =body.get("Customer_name",""),
                    Drop_off_Location = body.get("Dropoff_Location",""),
                    PickupLocation = body.get("Pickup_Location",""),
                    special_instructon = body.get("Special_Instruction",""),
                    Tax_Province=extract_tax_province(body.get("Pickup_Location","")),
                )

                # Create the order in zoho crm
                data = OrderApi.add_order(dict(OrderObj), token, release_forms, body.get("Vehicles",""))
                try:
                    job_id = data['zoho_order_id']

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
                    logger.info("---------Order added to DB-------------")
                    slack_msg = f"""🚚 *New Transport Request* \n *Details:* \n - Order ID: `{order_id}` \n - Transport Volume: `{len(body.get("Vehicles",""))}` vehicles \n - Pickup Location: `{OrderObj.PickupLocation}` \n - Drop-off Location: `{OrderObj.Drop_off_Location}` \n <https://crm.zohocloud.ca/crm/org110000402423/tab/Potentials/{job_id}|View Order Details>
                    """
                    send_message_to_channel(os.getenv("BOT_TOKEN"),os.getenv("CHANNEL_ID"),slack_msg)

                    return data
            
                except Exception as e:
                    logger.error(f"SQL DB Error: {e}")

        except Exception as e:
            logger.error(f"Func Main  Error: {e}")

            return {
                "error": str(e),
                "message": "Error Creating Order",
                "code": 500
            }
        
    


    async def _update_order(self, body:json) -> dict:
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
        

    async def _update_sql_order(self,body: dict):
        try:
            logger.info(f"body : {body}")
            with DatabaseConnection(connection_string=os.getenv("SQL_CONN_STR")) as session:
                logger.info("DB Connection established")
                primary_key_values = {
                    "OrderID": body.get("OrderID",""),
                }
                query = session.query(OrdersDB).filter_by(**primary_key_values).first()

                if not query:
                    logger.warning("No record found with the given primary key values")
                    return {"status": "error", "message": "Record not found"}
                
                            # Define updatable fields
                updatable_fields = [
                    "Status", "EstimatedDropoffTime", "EstimatedPickupTime", "CarrierID", "CarrierName", "CustomerPrice", "CarrierCost",
                    "ActualDeliveryTime", "ActualPickupTime",
                ]

                # Update the record dynamically
                for field in updatable_fields:
                    if field in body and body[field] is not None:
                        setattr(query, field, body[field])


                session.commit()
                logger.info("Record updated successfully")

                return {"status": "success", "message": "Record updated successfully"}

        except Exception as e:
            logger.error(f"Func Main  Error: {e}")

            return {
                "error": str(e),
                "message": "Error Updating Order",
                "code": 500
            }


    async def _delete_order(self):
        pass


class LeadAndQuote:

    def __init__(self):
        """
        Initialize the Lead and Quote handler class."""

    async def create_potential_carrier(self, body , carrierT: pd.DataFrame) -> dict:
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
        

                    try:
                        customer_body = body.get("Customer","")
                        customer_id = customer_body['id']
                        customer_name = customer_body['name']
                    except Exception as e:
                        customer_name = 'n/a'
                        customer_id = 'n/a'
                        logger.error(f"Error Creating Potential Carriers: {e}")

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
                try:
                    recommendation_df,pickup_city,destination_city = recommend_carriers(carrierT, pickup_location, dropoff_location)

                    with DatabaseConnection(connection_string=os.getenv("SQL_CONN_STR")) as session:
                        logger.info("Checking Existing Quote Availability")
                        # Query to fetch matching records
                        matching_quotes = session.query(TransportQuotation).filter(
                            and_(
                                TransportQuotation.QuoteStatus == "Active",
                                TransportQuotation.PickupCity.like(f"%{pickup_city}%"),
                                TransportQuotation.DestinationCity.like(f"%{destination_city}%")
                            )
                        ).all()
                       
                        if matching_quotes:
                            batch_quote = []
                            for quote in matching_quotes:
                                logger.info(f"{[quote.CarrierID],[quote.Estimated_Amount],[quote.EstimatedPickupTime],[quote.EstimatedDropoffTime],[quote.CreateDate]}")
                                
                                data = {
                                    "Name": f"{order_id}-{quote.CarrierName}",
                                    "VendorID": quote.CarrierID,
                                    "Pickup_Location": pickup_location,
                                    "Dropoff_Location": dropoff_location,
                                    "DealID": Zoho_Job_ID,
                                    "Estimated_Amount":quote.Estimated_Amount,
                                    "pickup_date_range":quote.EstimatedPickupTime,
                                    "Delivery_Date_Range":quote.EstimatedDropoffTime,
                                    "CreateDate":quote.CreateDate.strftime("%Y-%m-%d"),
                                    "Approval_Status":"Not sent",
                                    "Pickup_City":pickup_city,
                                    "Drop_off_City":destination_city,
                                    "Customer_Price_Excl_Tax":quote.CustomerPrice_excl_tax
                                }
                                batch_quote.append(data)
                            QuoteApi.create_quotes(token,batch_quote)
                            QuoteApi.update_deal(token,{"id":Zoho_Job_ID,"Stage":"Send Quote to Customer","Order_Status":"Quote Ready"})

                    if not recommendation_df.empty:
                        logger.info(f"before adding into zoho {recommendation_df['Carrier Name'].tolist()}")
                        recommendation_df["Carrier Name"] = recommendation_df["Carrier Name"].apply(standardize_name)
                        carrier_names = recommendation_df["Carrier Name"].tolist()
                        carriers = session.query(Vendor).filter(Vendor.VendorName.in_(carrier_names)).all()
                        carriers_with_ids = {c.VendorName: c.ZohoRecordID for c in carriers}
                        response = CleadApi.add_leads(recommendation_df,Zoho_Job_ID, token,carriers_with_ids)
                        return response
                except Exception as e:
                    logger.warning(f"Error While Generating Recommendations : {e}")
                    return {
                        "status":"failed",
                        "message": "No Potential Carrier Found",
                        "code": 500
                    }
            
        except Exception as e:
            logger.error(f"Func Main  Error: {e}")
            return {
                "error": str(e)
            }
    

    async def store_sql_quote(self, body : dict, carrierT: pd.DataFrame) -> func.HttpResponse:
        """ Handle quotes operations"""
        token = token_instance.get_access_token()
        try:
            with DatabaseConnection(connection_string=os.getenv("SQL_CONN_STR")) as session:
                logger.info(f"DB Connection established")
                try:
                    temp_df = carrierT[carrierT['Pickup City'].str.lower().isin(body.get("PickupLocation","-").lower().replace(",",'').split()) & 
                                       carrierT['Destination City'].str.lower().isin(body.get("DropoffLocation","-").lower().replace(",",'').split())]
                    # identified cities
                    pickup_city = temp_df['Pickup City'].iloc[0]
                    destination_city = temp_df['Destination City'].iloc[0]
                    logger.info(f"pickup city : {pickup_city} destination city : {destination_city}")
                    logger.info(extract_tax_province(body.get("PickupLocation","")))
                    ## search tax details 
                    tax = session.query(TaxDataBase).filter(TaxDataBase.province == extract_tax_province(body.get("PickupLocation",""))).first()
                    logger.info(f"tax : {tax}")

                    new_quote = TransportQuotation(
                        CarrierID=body.get("CarrierID","-"),
                        CarrierName=body.get("CarrierName","-"),
                        DropoffLocation=body.get("DropoffLocation","-"), 
                        PickupLocation=body.get("PickupLocation","-"),
                        EstimatedPickupTime=body.get("EstimatedPickupTime","-"),
                        EstimatedDropoffTime=body.get("EstimatedDropoffTime","-"),
                        Estimated_Amount=body.get("Estimated_Amount","-"),
                        PickupCity=pickup_city,
                        DestinationCity=destination_city,
                        TaxRate = tax.tax_rate ,
                        TaxName = tax.tax_name,
                        QuoteStatus = "ACTIVE",
                    )

                    try:
                        # Attempt to add the new quote
                        session.add(new_quote)
                        session.commit()
                        slack_msg = f"""💼📜 New Quote Added in Database! \n *Details* \n - Carrier Name: `{new_quote.CarrierName}` \n - Pickup City: `{new_quote.PickupCity}` \n - Destination City: `{new_quote.DestinationCity}` \n - Est. Amount: `{new_quote.Estimated_Amount}` \n - Est. Pickup Time: `{new_quote.EstimatedPickupTime}` \n - Est. Dropoff Time: `{new_quote.EstimatedDropoffTime}`"""
                        send_message_to_channel(os.getenv("BOT_TOKEN"),os.getenv("QUOTE_CHANNEL_ID"),slack_msg)

                    except IntegrityError:
                        # Rollback the session to clear the failed transaction
                        session.rollback()

                        # Handle duplicate: mark existing quotes as INACTIVE
                        session.query(TransportQuotation).filter(
                            and_(
                                TransportQuotation.PickupCity == new_quote.PickupCity,
                                TransportQuotation.DestinationCity == new_quote.DestinationCity,
                                TransportQuotation.CarrierName == new_quote.CarrierName,
                                TransportQuotation.QuoteStatus == "ACTIVE",
                            )
                        ).update({"QuoteStatus": "INACTIVE"})

                        # Commit the updates
                        session.commit()

                        # Retry adding the new quote
                        session.add(new_quote)
                        session.commit()
                        
                        slack_msg = f"""Overwrite Existing Quote in Database! \n *Details* \n - Carrier Name: `{new_quote.CarrierName}` \n - Pickup City: `{new_quote.PickupCity}` \n - Destination City: `{new_quote.DestinationCity}` \n - New Est. Amount: `{new_quote.Estimated_Amount}` \n - New Est. Pickup Time: `{new_quote.EstimatedPickupTime}` \n - New Est. Dropoff Time: `{new_quote.EstimatedDropoffTime}`"""
                        send_message_to_channel(os.getenv("BOT_TOKEN"),os.getenv("QUOTE_CHANNEL_ID"),slack_msg)

                    except Exception as e:
                        logger.error(f"Quote Creation SQL DB Error: {e}")

                        slack_msg = f"""❌ Error Adding Quote in Database! \n *Details* \n - Carrier Name: `{new_quote.CarrierName}` \n - Pickup City: `{new_quote.PickupCity}` \n - Destination City: `{new_quote.DestinationCity}` \n - Est. Amount: `{new_quote.Estimated_Amount}` \n - Est. Pickup Time: `{new_quote.EstimatedPickupTime}` \n - Est. Dropoff Time: `{new_quote.EstimatedDropoffTime}`"""
                        send_message_to_channel(os.getenv("BOT_TOKEN"),os.getenv("QUOTE_CHANNEL_ID"),slack_msg)

                    QuoteApi.update_quote(token,{
                        "id":body.get("QuotationRequestID","-"),
                        "Pickup_City":pickup_city,
                        "Drop_off_City":destination_city
                    })

                    return {
                        "status":"success",
                        "message": "Quote Created Successfully",
                        "code": 200
                    }
                except Exception as e:
                    raise Exception(f"Error creating Quotes: {e}")
                

        except Exception as e:
            logger.error(f"Quote Creation Error: {e}")
            slack_msg = f""" ❌ Error Adding Quote in Database! \n *Details* \n - Carrier Name: `{body.get('CarrierName','-')}` \n - Pickup City: `{body.get('PickupLocation','-')}` \n - Destination City: `{body.get('DropoffLocation','-')}` \n *Error:* {str(e)}"""
            send_message_to_channel(os.getenv("BOT_TOKEN"),os.getenv("QUOTE_CHANNEL_ID"),slack_msg)
            return {
                        "status":"failed",
                        "message": "Quote Creation Failed",
                        "code": 500,
                        "error": str(e)
                    }


    async def update_sql_quote(self,body: dict):
        try:
            logger.info(f"body : {body}")
            # Extract data from the input
            primary_key_values = {
                "CarrierName": body.get("CarrierName"),
                "PickupCity": body.get("PickupCity"),
                "DestinationCity": body.get("DestinationCity"),
                "QuoteStatus": "ACTIVE",
            }
            customerprice = body.get("Customer_Price")

            # Establish the database connection
            with DatabaseConnection(connection_string=os.getenv("SQL_CONN_STR")) as session:
                logger.info("DB Connection established")

                # Find the record by composite primary key
                query = session.query(TransportQuotation).filter_by(**primary_key_values).first()

                if not query:
                    logger.warning("No record found with the given primary key values")
                    return {"status": "error", "message": "Record not found"}
                
                try:
                    query.CustomerPrice_excl_tax = float(customerprice)
                    query.TaxAmount = query.CustomerPrice_excl_tax * (query.TaxRate/100)
                    query.TotalAmount = query.TaxAmount + query.CustomerPrice_excl_tax
                except Exception as e:
                    logger.warning(f"Error converting Customer Price to float: {e}")

                if body.get("Approval_status") == "Accepted":
                    query.Rating = query.Rating + 1

                # Commit the changes
                session.commit()
                logger.info("Record updated successfully")

                return {"status": "success", "message": "Record updated successfully"}

        except Exception as e:
            logger.error(f"Database error occurred: {e}")
            return {"status": "error", "message": "Database error occurred"}
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return {"status": "error", "message": "Unexpected error occurred"}
    
    async def get_quote(self,body: dict):
        try:

            pickup_city = body.get("PickupCity")
            dropoff_city = body.get("DestinationCity")
            
            with DatabaseConnection(connection_string=os.getenv("SQL_CONN_STR")) as session:
                logger.info("DB Connection established")
                query = session.query(TransportQuotation).filter(
                    and_(
                        TransportQuotation.PickupCity == pickup_city,
                        TransportQuotation.DestinationCity == dropoff_city,
                        TransportQuotation.QuoteStatus == "ACTIVE",
                    )
                ).order_by(TransportQuotation.Rating.asc()).first() 
                
                if not query:
                    logger.warning("No record found with the given pickup and destination cities")
                    return {"status": "error", "message": "no quote found"}
                
                return {
                    "status": "success",
                    "quote":{
                        "CarrierName":query.CarrierName,
                        "Estimated_Amount":query.Estimated_Amount,
                        "EstimatedPickupTime":query.EstimatedPickupTime,
                        "EstimatedDropoffTime":query.EstimatedDropoffTime,
                        "PickupCity":query.PickupCity,
                        "DestinationCity":query.DestinationCity,
                        "tax_rate":query.TaxRate,
                        "tax_name":query.TaxName,
                        "tax_amount":query.TaxAmount,
                        "total_amount":query.TotalAmount,
                        "CustomerPrice_excl_tax":query.CustomerPrice_excl_tax,
                        "Currency":query.Currency
                    },
                    "code": 200
                }
    
        except Exception as e:
            logger.error(f"Func Main  Error: {e}")
            return {
                "error": str(e)
            }
