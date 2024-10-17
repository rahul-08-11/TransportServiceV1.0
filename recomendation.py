import pandas as pd
import numpy as np

def transport_eff_m(avg_day, max_day, min_day,count_requests):
    if pd.isna(avg_day):  # Handle NaN values
        return 0
    elif min_day == max_day and isinstance(avg_day, float):
        return 5  # Neutral score if all values are the same
    else:
        raw_trasport_eff =  max(0, 5 - (avg_day / max_day) * 5)  # Avoid negative scores
        scaling_factor = 1 - round(1 / (1 + round(np.exp(-(count_requests -10)))),3)  # low request counts

        teff= raw_trasport_eff - raw_trasport_eff * scaling_factor
        print(teff,scaling_factor)
        if avg_day < 2 and count_requests < 6:
            return teff*0.3
        return teff

def cost_eff_m(estimated_cost, max_cost, min_cost):
    if pd.isna(estimated_cost):
        return 0
    elif min_cost == max_cost and isinstance(estimated_cost, float):
        return 5  # Neutral score if all values are the same
    else:
        # Calculate the raw cost efficiency score without scaling factor
        raw_cost_eff = max(0, 10 - (estimated_cost / max_cost) * 10)  # Avoid negative scores

        return max(0, raw_cost_eff)  # Ensure the score is not negative


def reliability_m(on_time, late_delivery, count_requests):
      if (on_time + late_delivery) == 0 or pd.isna(late_delivery) or pd.isna(on_time):
          return 0  # No data for reliability
      raw_reliability = (on_time / (on_time + late_delivery)*5) # 0 - 1

      scale_factor =1- round(1 / (1 + np.exp(-(count_requests -3))),3)  # dampen score for low request counts
     
      return raw_reliability - raw_reliability * scale_factor


def categorize_intensity(score_value : float) -> str:
    if score_value >= 14:
        return "Hot"
    elif score_value >= 7 and score_value <= 13:
        return "Warm"
    else:
        return "Cold"
    
def normalize_text(text):
    if isinstance(text, str):
        return text.lower().strip().replace("é", "e")
    return text


from utils.helpers import get_logger
logger = get_logger(__name__)
def recommend_carriers(carrierT, pickup_city, destination_city):

    # Filter for the specific pickup and destination city
    recommended_carriers = carrierT[
        (carrierT['Pickup City'].str.lower().str.strip().str.replace("é", "e").str.contains(normalize_text(pickup_city))) &
        (carrierT['Destination City'].str.lower().str.strip().str.replace("é", "e").str.contains(normalize_text(destination_city)))
    ].copy()
    logger.info(recommended_carriers['Carrier Name'])
    # Transport efficiency score calculation
    recommended_carriers['Transport Eff. Score'] = recommended_carriers.apply(
        lambda row: transport_eff_m(row['Avg. Delivery Day'], recommended_carriers['Avg. Delivery Day'].max(), recommended_carriers['Avg. Delivery Day'].min(), count_requests=row['CountRequest'
        ]),axis=1) 
    
    # Reliability score calculation 
    recommended_carriers['Reliability Score'] = recommended_carriers.apply(
        lambda row: reliability_m(row['On-time'], row['Late Delivery'], row['CountRequest']),axis=1
        )


     # Cost efficiency score calculation
    recommended_carriers['Cost Eff. Score'] = recommended_carriers.apply(
        lambda row: cost_eff_m(row['Estimated Amount'],
                                max_cost=recommended_carriers['Estimated Amount'].max(),
                                min_cost=recommended_carriers['Estimated Amount'].min(),
                ),
        axis=1
    )

    # Clean up unnecessary columns and calculate final score
    recommended_carriers = recommended_carriers.drop(columns=["Avg. Cost Per Km", "Transport Requests"], errors='ignore')

    # Calculate final score with weights (adjust weights as necessary)
    recommended_carriers['CScore'] = (
        recommended_carriers['Transport Eff. Score']  +
        recommended_carriers['Reliability Score']  +
        recommended_carriers['Cost Eff. Score'] 
    )

    # Sort by final score
    recommended_carriers =  recommended_carriers.sort_values(by='CScore', ascending=True)
    recommended_carriers = recommended_carriers.drop(columns=['Pickup City','Pickup State/Province','Pickup Country','Destination City','Destination State/Province','Destination Country'])

    recommended_carriers['Lead Score'] = recommended_carriers['CScore'].apply(categorize_intensity)
    logger.info(recommended_carriers['Carrier Name'])

    return recommended_carriers