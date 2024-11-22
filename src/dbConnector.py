
from sqlalchemy import create_engine, Column, String, DateTime, PrimaryKeyConstraint, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import func as sqlfunc
import logging


Base = declarative_base()

class DatabaseConnection:
    # Class variable to hold the engine
    engine = None

    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.session = None

        # Create the engine only once when the class is first initialized
        if DatabaseConnection.engine is None:
            DatabaseConnection.engine = create_engine(
                self.connection_string,
                pool_size=10,          # Max connections to keep in the pool
                max_overflow=5,       # Max additional connections beyond pool_size
                pool_timeout=30,      # Timeout for getting a connection
                pool_recycle=1800     # Recycle connections every 30 minutes
            )

    def __enter__(self):
        self.session = sessionmaker(bind=DatabaseConnection.engine)()
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logging.error(f"Error occurred: {exc_val}")
            if self.session:
                self.session.rollback()
        if self.session:
            self.session.close()




## ORM classes
class Carriers(Base):
    __tablename__ = 'Carriers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    CarrierName = Column(String(255), nullable=False)
    NumTransportjobs = Column(String(255), nullable=True)
    ZohoRecordID = Column(String(255), nullable=True)



class OrdersDB(Base):
    __tablename__ = 'TransportOrders'
    OrderID = Column(String(255), primary_key=True, nullable=False)  # No autoincrement here
    TransportRequestID = Column(String(255), nullable=False, unique=True)  # Ensure this is unique
    CustomerID = Column(String(255), nullable=True)
    CustomerName = Column(String(255), nullable=True)
    CreateTime = Column(DateTime, default=sqlfunc.now(), nullable=False)
    EstimatedPickupTime = Column(String(255), nullable=True)
    EstimatedDropoffTime = Column(String(255), nullable=True)
    JobPrice = Column(String(255), nullable=True)
    CarrierCost = Column(String(255), nullable=True)
    Status = Column(String(255), nullable=True)
    PickupLocation = Column(String(255), nullable=True)
    DropoffLocation = Column(String(255), nullable=True)
    ActualPickupTime = Column(DateTime, nullable=True)
    ActualDeliveryTime = Column(DateTime, nullable=True)
    CarrierName = Column(String(255), nullable=True)
    CarrierID = Column(String(255), nullable=True)


class TransportQuotation(Base):
    __tablename__ = 'TransportQuotation'

    # Define both columns as part of the composite primary key
    TransportRequestID = Column(String(255), primary_key=True, nullable=False)
    CreateTime = Column(DateTime, default=sqlfunc.now(), nullable=False)
    CarrierName = Column(String(255), nullable=False)
    DropoffLocation = Column(String(255), nullable=True)
    PickupLocation = Column(String(255), nullable=True)
    EstimatedPickupTime = Column(String(255), nullable=True)
    EstimatedDropoffTime = Column(String(255), nullable=True)
    Estimated_Amount = Column(String(255), nullable=True)


