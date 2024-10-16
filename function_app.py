import azure.functions as func
from src.funcmain import *
import azure.durable_functions as df
import pandas as pd
from azure.storage.blob import BlobServiceClient, BlobClient
import os
app = df.DFApp(http_auth_level=func.AuthLevel.ANONYMOUS)
# from dotenv import load_dotenv
# load_dotenv()


# Example usage:
blob_service_client = BlobServiceClient.from_connection_string(os.getenv("BLOB_CONN_STR"))

logger = get_logger(__name__)


# HTTP-triggered function with a Durable Functions client binding
@app.route(route="orchestrators/{functionName}")
@app.durable_client_input(client_name="client")
async def http_start(req: func.HttpRequest, client):
    function_name = req.route_params.get('functionName')

    details = {
        "ContainerName":"carriersfiles",
        "blobName":"CarriersT.csv",
        "Location":"carriersBlob.csv"
    }

    try:
        # Check if there's already a running instance
        existing_instances = await client.get_status_all()
        for instance in existing_instances:
            if instance.runtime_status == "Running":
                # Terminate the running instance
                await client.terminate(instance.instance_id, "Stopping previous instance to start a new one.")

        # Start a new orchestration instance
        instance_id = await client.start_new(function_name, None,details)

        return func.HttpResponse(f"Orchestration Instance started: {instance_id}")
    
    except Exception as e:
        logging.error(f"Failed to start orchestration: {e}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)

# Orchestrator
@app.orchestration_trigger(context_name="context")
def Order_orchestrator(context):
    details = context.get_input()
    yield context.call_activity("fetch_carrierT_activity",details)
    yield context.call_activity("store_carrier_activity",details)
    return ['Completed']




# Activity functions
@app.activity_trigger(input_name="details")
def fetch_carrierT_activity(details: dict):
    logging.info(f"Activity 'fetch_carrier_activity' triggered with details: {details}")

        # Create a BlobClient
    blob_client = blob_service_client.get_blob_client(container=details['ContainerName'], blob=details['blobName'])
    
    # Get blob properties
    props = blob_client.get_blob_properties()  # Use BlobClient here
    blob_size = props.size  # Access size from the properties
    chunk_size = 256 * 1024   # 64 KB chunk size
    index = 0

    with open(details['Location'], 'wb') as f:
        while index < blob_size:
            range_start = index
            range_end = min(index + chunk_size - 1, blob_size - 1)
            range_header = f'bytes={range_start}-{range_end}'
            data = blob_client.download_blob(offset=range_start, length=chunk_size).readall()  # Download in chunks
            
            length = len(data)
            index += length
            logger.info(f"index is {index}")
            
            if length > 0:
                f.write(data)
                if length < chunk_size:
                    break
            else:
                break
    return f"{index}"




@app.activity_trigger(input_name="details")
def store_carrier_activity(details: dict):
    global carrierT
    carrierT = pd.read_csv(details["Location"])
    logging.info(f"Stored carrierT : {len(carrierT)}")
    return f"Length of carrierT: {len(carrierT)}"


@app.route(route="ping", methods=['GET'])
async def ping(req: func.HttpRequest) -> func.HttpResponse:
    logger.info('Ping request received.')
    return func.HttpResponse("Service is up", status_code=200)



@app.route(route="Order", methods=["POST"])
async def Order_Operation(req: func.HttpRequest) -> func.HttpResponse:
    logger.info(f"Request received from {req.url}")
    body = req.get_json()
    logger.info(f"body : {body}")

    if req.params.get("action") == "create":

        try:
            response = await create_order(body)
            logger.info(f"Func app :{response}")
            return func.HttpResponse(json.dumps(response), status_code=200)

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return func.HttpResponse("Internal server error", status_code=500)

    elif req.params.get("action") == "update":
        try:
            response = await update_order(body)
        
            return func.HttpResponse(json.dumps(response), status_code=200)

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return func.HttpResponse("Internal server error", status_code=500)

    else:
        return func.HttpResponse("Invalid request", status_code=400)
    


@app.route(route="Clead", methods=["POST"])
async def CarrierLead(req: func.HttpRequest) -> func.HttpResponse:
    logger.info(f"Request received from {req.url}")
        
    body = req.get_json()
    logger.info(f"body : {body}")
    try:
        response = await create_potential_carrier(body,carrierT)

        logger.info(f"Func app :{response}")
        return func.HttpResponse(json.dumps("TEST"), status_code=200)

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)



@app.route(route="operations", methods=["POST"])
async def Operations(req: func.HttpRequest) -> func.HttpResponse:
    
    logger.info(f"Request received from {req.url}")
    body = req.get_json()
    logger.info(f"body : {body}")
    
    return func.HttpResponse(json.dumps(body), status_code=200)

