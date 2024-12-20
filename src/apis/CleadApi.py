import requests
from utils.helpers import *

logger = get_logger(__name__)

CLEADS_URL="https://www.zohoapis.ca/crm/v2/Potential_Carrier"



def get_carrier_id(access_token :str, unique_identifier : str, field_name :str):
    """
    unique_identifier : Primary key to search
    field_name : Name of the field to be searched
    """
    # API endpoint
    url = "https://www.zohoapis.ca/crm/v2/Vendors/search"

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
def add_leads(recom_df, job_id, token, carriers_with_ids):
    headers = {
        "Authorization": f"Zoho-oauthtoken {token}",
        "Content-Type": "application/json",
    }
    data = []
    success_leads = 0
    logger.info(f"length of recommendation generated is {len(recom_df)}")
    logger.info(recom_df['Carrier Name'].tolist())
    for index, row in recom_df.iterrows():
        try:
            carrier_name = row["Carrier Name"]
            Lead_Name = f"{standardize_name(carrier_name)}"
            lead_data = {
                "VendorID": carriers_with_ids[carrier_name],
                "Name": Lead_Name,
                "Carrier_Score": row['Lead Score'], # assing score
                "Transport_Job_in_Deal": job_id,
                "Progress_Status": "To Be Contacted",
            }
            data.append(lead_data)
            logger.info(f"data {lead_data}")
            success_leads += 1
        except Exception as e:
            logger.error(f"Error Adding/Parsing lead: {e}")

    payload = {"data": data}

    response = requests.post(CLEADS_URL, headers=headers, json=payload)
    data = response.json()
    try:
        if response.status_code in [200, 201]:
            logger.info(f"Successfully added {success_leads} leads for Job {job_id}")
            for i, lead in enumerate(data["data"]):
                lead_id = lead["details"]["id"]
                recom_df.loc[i, "Lead_ID"] = lead_id
        else:
            print(f"Failed to add leads for {response.json()}")

    except Exception as e:
        print(f"Error sending request: {e}")

    return data
