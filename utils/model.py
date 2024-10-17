from pydantic import BaseModel, Field
from typing import Optional


class Order(BaseModel):
    OrderID : Optional[str] = None
    Customer_id : Optional[str] = None
    Customer_Name: Optional[str] = None
    Dropoff_Location : Optional[str] = None
    Order_ID : Optional[str] = None
    Pickup_Location : Optional[str] = None
    Shipment_Status : Optional[str] = "Pending"
    carrier_paid_status	: Optional[str] = "Unpaid"
    customer_paid_status : Optional[str] = "Unpaid"
    Name : Optional[str] = None
    Vehicle_Details : Optional[list] = None
    Customer_Notes : Optional[str] = None



class Clead(BaseModel):
    Carrier_Score	: Optional[str] = None
    Progress_Status : Optional[str] = "To Be Contacted"
    Zoho_Job_ID: Optional[str] = None
    Name : Optional[str] = None
    Pickup_Location : Optional[str] = None
    Dropoff_Location : Optional[str] = None
    Vehicle_Details : Optional[dict] = None
    Estimated_Amount : Optional[str] = None   