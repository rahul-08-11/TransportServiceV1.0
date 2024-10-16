# utils/helpers.py
import re
import logging
import datetime
from sqlalchemy import create_engine, Column, String, DateTime, PrimaryKeyConstraint, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import func as sqlfunc

logger = logging.getLogger(__name__)

Base = declarative_base()
def standardize_name(name):
    name = name.title()  # Capitalize the first letter of each word
    # Remove punctuation except hyphens
    name = re.sub(r"[^\w\s-]", '', name)  # Keeps hyphens, removes other punctuation
    # Remove extra spaces
    name = re.sub(r'\s+', ' ', name)  # Replace multiple spaces with a single space
    name = name.strip()  # Remove leading and trailing spaces
    return name

# Function to configure logging
def get_logger(name):
    # Create a logger
    logger = logging.getLogger(name)
    
    # If the logger already has handlers, don't add more (this avoids duplicate logs)
    if not logger.hasHandlers():
        # Set logging level
        logger.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter and add it to the handler
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        
        # Add the console handler to the logger
        logger.addHandler(console_handler)
    
    return logger

    
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

    # Define a relationship to TransportQuotation
    quotations = relationship("TransportQuotation", back_populates="order")


class TransportQuotation(Base):
    __tablename__ = 'TransportQuotation'
    
    # Define both columns as part of the composite primary key
    TransportRequestID = Column(String(255), ForeignKey('TransportOrders.TransportRequestID'), nullable=False)
    CarrierName = Column(String(255), nullable=False)

    DropoffLocation = Column(String(255), nullable=True)
    PickupLocation = Column(String(255), nullable=True)
    ActualPickupTime = Column(DateTime, nullable=True)
    ActualDropoffTime = Column(DateTime, nullable=True)
    EstimatedPickupTime = Column(DateTime, nullable=True)
    EstimatedDropoffTime = Column(DateTime, nullable=True)
    Price_Quotes = Column(String(255), nullable=True)
    Notes = Column(String(255), nullable=True)

    # Define a composite primary key
    __table_args__ = (
        PrimaryKeyConstraint('TransportRequestID', 'CarrierName'),
    )

    # Define a relationship back to Orders
    order = relationship("OrdersDB", back_populates="quotations")




def get_order_id(session):
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

    order_id = f"#{order_id}"
    return order_id