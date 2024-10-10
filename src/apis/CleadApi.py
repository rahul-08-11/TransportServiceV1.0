import requests
from utils.helpers import *

logger = get_logger(__name__)


def get_carrier_id(access_token :str, unique_identifier : str, field_name :str):
    """
    unique_identifier : Primary key to search
    field_name : Name of the field to be searched

    """
    # API endpoint
    url = "https://www.zohoapis.ca/crm/v2/Carriers/search"

    params = {"criteria": f"{field_name}:equals:{unique_identifier}"}

    # Authorization Header
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
    }

    # Make GET request to fetch id
    response = requests.get(url, params=params, headers=headers)

    # Check if request was successful
    if response.status_code == 200 or response.status_code == 201:
        data = response.json()
        if data["data"]:
            carrier_id = data["data"][0]["id"]
            return carrier_id
        else:
            return None
    else:
        print(response)


## batch request
def add_leads(recommendation_df, job_id, token):
    url = "https://www.zohoapis.ca/crm/v2/Potential_Carrier"

    headers = {
        "Authorization": f"Zoho-oauthtoken {token}",
        "Content-Type": "application/json",
    }

    data = []
    success_leads = 0

    for index, row in recommendation_df.iterrows():
        try:
            carrier_name = row["Carrier Name"]
            carrier_id = get_carrier_id(token, carrier_name, "Account_Name")

            if buyer_id:
                lead_data = {
                    "Carrier":carrier_id,
                    "Name": job_id + standardize_name(carrier_name),
                    "Vehicle_State": "Available",
                    "Carrier_Score": buyer_name, # assing score
                    "Transport_Job": job_id,
                    "Progress_Status": "To Be Contacted"
                }
                data.append(lead_data)
                success_leads += 1
        except Exception as e:
            print(e)

    payload = {"data": data}

    response = requests.post(url, headers=headers, json=payload)
    data = response.json()
    try:
        if response.status_code in [200, 201]:
            print(f"Successfully added {success_leads} leads for Job {job_id}")
            for i, lead in enumerate(data["data"]):
                lead_id = lead["details"]["id"]
                recommendation_df.loc[i, "Lead_ID"] = lead_id
        else:
            print(f"Failed to add leads for {response.json()}")

    except Exception as e:
        print(f"Error sending request: {e}")

    return data
