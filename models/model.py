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
    Make : Optional[str] = None
    Model : Optional[str] = None
    Payment_Status : Optional[str] = None
    Pickup_Location : Optional[str] = None
    Scheduled_Dropoff_Time : Optional[str] = None
    Scheduled_Pickup_Time : Optional[str] = None
    Shipment_Status : Optional[str] = None
    Name : Optional[str] = None
    Trim : Optional[str] = None
    Vin : Optional[str] = None
    Year: Optional[str] = None