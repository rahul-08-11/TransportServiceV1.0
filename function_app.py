# import azure.functions as func
# import azure.durable_functions as df
# import logging
# import asyncio

# myApp = df.DFApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# # An HTTP-triggered function with a Durable Functions client binding
# @myApp.route(route="orchestrators/{functionName}")
# @myApp.durable_client_input(client_name="client")
# async def http_start(req: func.HttpRequest, client):
#     function_name = req.route_params.get('functionName')

#     order_details =  req.get_json()
#     instance_id = await client.start_new(function_name,input=order_details)

#     # Polling to wait until the orchestration is completes
#     while True:
#         status = await client.get_status(instance_id)
#         logging.info(f"Orchestration status: {status.runtime_status}")
        
#         # Exit the loop if the orchestration has completed, failed, or terminated
#         if any(status.runtime_status in state for state in ['Completed', 'Failed', 'Terminated']):
#             break

#         await asyncio.sleep(0.1)  # Poll every 0.1 seconds

#     return func.HttpResponse(f"Orchestration completed with result: {status.output}")
  
# # Orchestrator
# @myApp.orchestration_trigger(context_name="context")
# def Order_orchestrator(context):
#     order_details = context.get_input()
#     result1 = yield context.call_activity("add_order_activity", order_details)

#     result2 = yield context.call_activity("update_orderId_activity", '892489')


#     return [result2]

# # Activity
# @myApp.activity_trigger(input_name="Order_details")
# def add_order_activity(Order_details: str):
#     logging.info(f"Activity 'add_order_activity' triggered for city: {Order_details}")
#     return f"{Order_details}"


# @myApp.activity_trigger(input_name="OrderId")
# def update_orderId_activity(OrderId: str):
#     logging.info(f"Activity 'update_orderId_activity' triggered for city: {OrderId}")
#     return f"Hello {OrderId}"




import azure.functions as func
from src.funcmain import *
from utils.helpers import *


logger = get_logger(__name__)

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)



@app.route(route="ping", methods=['GET'])
async def ping(req: func.HttpRequest) -> func.HttpResponse:
    logger.info('Ping request received.')
    return func.HttpResponse("Service is up", status_code=200)




@app.route(route="Order", methods=["POST"])
async def Order_Operation(req: func.HttpRequest) -> func.HttpResponse:
    logger.info(f"Request received from {req.url}")
    body = req.get_json()
    if req.params.get("action") == "create":

        try:
            response = await create_order(body)

            Order_Id = response["data"][0]["details"]["id"]
            update_id = {
                "id": Order_Id,
                "OrderID": Order_Id
            }
            await update_order(update_id)
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