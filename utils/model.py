from pydantic import BaseModel, Field
from typing import Optional


class Order(BaseModel):
    Deal_Name : Optional[str] = None
    Customer_id : Optional[str] = None
    Customer_Name: Optional[str] = None
    Dropoff_Location : Optional[str] = None
    Pickup_Location : Optional[str] = None
    Stage : Optional[str] = "Pending"
    Carrier_Payment_Status	: Optional[str] = "Unpaid"
    Customer_Payment_Status	 : Optional[str] = "Unpaid"
    Name : Optional[str] = None
    Orders : Optional[list] = None
    Customer_Notes : Optional[str] = None
    Vehicle_Subform : Optional[list] = None



class Clead(BaseModel):
    Carrier_Score	: Optional[str] = None
    Progress_Status : Optional[str] = "To Be Contacted"
    Zoho_Job_ID: Optional[str] = None
    Name : Optional[str] = None
    Pickup_Location : Optional[str] = None
    Dropoff_Location : Optional[str] = None
    Vehicle_Details : Optional[dict] = None