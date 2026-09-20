import pandas as pd
import requests

def load_facilities(url):
    """
    This function pulls facilities data from compute-atlas's API.
    Their GitHub: https://github.com/ek33450505/compute-atlas
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # normalize JSON column to create separate columns in CSV
        if isinstance(data, dict):
            records = data.get('facilities') or data.get('data') or data.get('results') or data
        else:
            records = data
        
        facilities_df = pd.json_normalize(records, sep='_')
        print("Facilities data pulled from API")
        return facilities_df
    except requests.exceptions.RequestException as e:
        print(f"Error loading facilities data: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    url = "https://compute-atlas.com/api/facilities"
    data = load_facilities(url)
    data.to_csv("Data/facilities_data.csv", index=False)
    print("Data written to Data/facilities_data.csv")