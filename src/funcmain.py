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
                    slack_msg = f"""
                    🚚 *New Transport Request*

            *Details:*
            - Order ID: `{order_id}`
            - Transport Volume: `{len(body.get("Vehicles",""))}` vehicles
            - Pickup Location: `{OrderObj.PickupLocation}`
            - Drop-off Location: `{OrderObj.Drop_off_Location}`

            <https://crm.zohocloud.ca/crm/org110000402423/tab/Potentials/{job_id}|View Order Details>

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
                    recommendation_df,pickupcity,dropoffcity = recommend_carriers(carrierT, pickup_location, dropoff_location)

                    with DatabaseConnection(connection_string=os.getenv("SQL_CONN_STR")) as session:
                        logger.info("Checking Existing Quote Availability")

                        # Subquery to get the latest CreateTime for each group
                        subquery = session.query(
                            TransportQuotation.CarrierID,
                            TransportQuotation.PickupCity,
                            TransportQuotation.DestinationCity,
                            sqlfunc.max(TransportQuotation.CreateDate).label("MaxCreateTime")
                        ).group_by(
                            TransportQuotation.CarrierID,
                            TransportQuotation.PickupCity,
                            TransportQuotation.DestinationCity
                        ).subquery()

                        # Main query to fetch matching records with the latest CreateTime
                        matching_quotes = session.query(TransportQuotation).join(
                            subquery,
                            and_(
                                TransportQuotation.CarrierID == subquery.c.CarrierID,
                                TransportQuotation.PickupCity == subquery.c.PickupCity,
                                TransportQuotation.DestinationCity == subquery.c.DestinationCity,
                                TransportQuotation.CreateDate == subquery.c.MaxCreateTime
                            )
                        ).filter(
                            TransportQuotation.PickupLocation.like(f"%{pickupcity}%"),
                            TransportQuotation.DropoffLocation.like(f"%{dropoffcity}%")
                        ).all()

                        if matching_quotes:
                            batch_quote = []
                            for quote in matching_quotes:
                                logger.info(f"{[quote.CarrierID],[quote.Estimated_Amount],[quote.EstimatedPickupTime],[quote.EstimatedDropoffTime],[quote.CreateDate]}")
                                
                                data = {
                                    "Name": f"{order_id}-{quote.CarrierName}",
                                    "Carriers": quote.CarrierID,
                                    "Pickup_Location": pickup_location,
                                    "Dropoff_Location": dropoff_location,
                                    "Transport_Job_in_Deal": Zoho_Job_ID,
                                    "Estimated_Amount":quote.Estimated_Amount,
                                    "pickup_date_range":quote.EstimatedPickupTime,
                                    "Delivery_Date_Range":quote.EstimatedDropoffTime,
                                    "CreateDate":quote.CreateDate.strftime("%Y-%m-%d"),
                                    "Approval_Status":"Not sent"
                                }
                                batch_quote.append(data)
                            QuoteApi.create_quotes(token,batch_quote)
                            QuoteApi.update_deal(token,{"id":Zoho_Job_ID,"Stage":"Send Quote to Customer"})

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
    

    async def quotes_operation(self, body : dict, carrierT: pd.DataFrame) -> func.HttpResponse:
        """ Handle quotes operations"""
        token = token_instance.get_access_token()
        try:
            with DatabaseConnection(connection_string=os.getenv("SQL_CONN_STR")) as session:
                logger.info(f"DB Connection established")
                try:
                    temp_df = carrierT[carrierT['Pickup City'].str.lower().isin(body.get("PickupLocation","-").lower().replace(",",'').split()) & carrierT['Destination City'].str.lower().isin(body.get("DropoffLocation","-").lower().replace(",",'').split())]
                    # identified cities
                    pickup_city = temp_df['Pickup City'].iloc[0]
                    destination_city = temp_df['Destination City'].iloc[0]
        
                    quote = TransportQuotation(
                        CarrierID=body.get("CarrierID","-"),
                        QuotationRequestID=body.get("QuotationRequestID","-"),
                        CarrierName=body.get("CarrierName","-"),
                        DropoffLocation=body.get("DropoffLocation","-"), 
                        PickupLocation=body.get("PickupLocation","-"),
                        EstimatedPickupTime=body.get("EstimatedPickupTime","-"),
                        EstimatedDropoffTime=body.get("EstimatedDropoffTime","-"),
                        Estimated_Amount=body.get("Estimated_Amount","-"),
                        PickupCity=pickup_city,
                        DestinationCity=destination_city,
                        TaxRate = body.get("Tax_Rate"),
                        TaxName = body.get("Tax_Name")
                    )
                    session.add(quote)
                    session.commit()
                    ## update pickup and dropoff city
                    QuoteApi.update_quote(token,{
                        "id":body.get("QuotationRequestID","-"),
                        "Pickup_City":pickup_city,
                        "Drop_off_City":destination_city
                    })
                except Exception as e:
                    logger.error(f"Quote Creation Error: {e}")

        except Exception as e:
            logger.error(f"Quote Creation Error: {e}")



    async def update_sql_quote(self,body: dict):
        try:
            logger.info(f"body : {body}")
            # Extract data from the input
            primary_key_values = {
                "EstimatedPickupTime": body.get("EstimatedPickupTime"),
                "EstimatedDropoffTime": body.get("EstimatedDropoffTime"),
                "PickupCity": body.get("PickupCity"),
                "DestinationCity": body.get("DestinationCity"),
                "Estimated_Amount": body.get("OldEstimatedAmount"),
                "CarrierID": body.get("CarrierID"),
            }
            tax_amount = body.get("Tax_Amount")
            tax_rate = body.get("Tax_Rate")
            tax_name = body.get("Tax_Name")
            customerprice = body.get("Customer_Price")
            total_amount = body.get("Total_Amount")

            # Establish the database connection
            with DatabaseConnection(connection_string=os.getenv("SQL_CONN_STR")) as session:
                logger.info("DB Connection established")

                # Find the record by composite primary key
                query = session.query(TransportQuotation).filter_by(**primary_key_values).first()

                if not query:
                    logger.warning("No record found with the given primary key values")
                    return {"status": "error", "message": "Record not found"}

                # Update the fields
                query.TaxAmount = tax_amount
                query.TaxRate = tax_rate
                query.TaxName = tax_name
                query.CustomerPrice_excl_tax = customerprice
                query.TotalAmount = total_amount
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