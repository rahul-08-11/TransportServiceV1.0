from pydantic import BaseModel, Field
from typing import Optional


class Order(BaseModel):
    OrderID : Optional[str] = None
    Customer_id : Optional[str] = None
    Customer_Name: Optional[str] = None
    Actual_Dropoff_Time : Optional[str] = None
    Actual_Pickup_Time	:Optional[str] = None
    Dropoff_Location : Optional[str] = None
    Email : Optional[str] = None
    Job_Price : Optional[str] = None
    Order_ID : Optional[str] = None
    Payment_Status : Optional[str] = None
    Pickup_Location : Optional[str] = None
    Scheduled_Dropoff_Time : Optional[str] = None
    Scheduled_Pickup_Time : Optional[str] = None
    Shipment_Status : Optional[str] = None
    Name : Optional[str] = None
    Vehicle_Details : Optional[list] = None



class Clead(BaseModel):
    Carrier_Score	: Optional[str] = None
    Progress_Status : Optional[str] = "To Be Contacted"
    Zoho_Job_ID: Optional[str] = None
    Name : Optional[str] = None
    Pickup_Location : Optional[str] = None
    Dropoff_Location : Optional[str] = None
    Vehicle_Details : Optional[dict] = None