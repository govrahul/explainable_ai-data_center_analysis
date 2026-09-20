"""
This file requires the creation of an EIA API key. To create this, please go to: https://www.eia.gov/opendata/register.php
"""

import pandas as pd
import requests
import os
from dotenv import load_dotenv

# load API key from .env file in base directory
load_dotenv('.env')
API_KEY = os.getenv('EIA_API_KEY')

# 2. Standard EPA Emission Factors (lbs CO2 per MMBtu)
FUEL_EMISSION_FACTORS = {
    'NG': 117.0,   # Natural Gas
    'BIT': 205.7,  # Bituminous Coal
    'SUB': 214.3,  # Subbituminous Coal
    'LIG': 215.4,  # Lignite Coal
    'DFO': 161.3,  # Distillate Fuel Oil / Diesel
    'RFO': 173.7,  # Residual Fuel Oil
    'JF': 156.4,   # Jet Fuel
    'WO': 173.7,   # Waste Oil
}

def fetch_year_data(api_key, year):
    """
    Queries EIA API v2 for a given year's monthly state-level generation 
    and fuel consumption data.
    """
    url = "https://api.eia.gov/v2/electricity/facility-fuel/data/"
    
    params = {
        "api_key": api_key,
        "frequency": "monthly",
        "data[0]": "generation",
        "data[1]": "total-consumption-btu",
        "start": f"{year}-01",
        "end": f"{year}-12",
        "length": 5000  # Captures all state/fuel combinations in one page
    }

    print(f"Fetching data for {year}...")
    try:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"API Error ({response.status_code}) for year {year}: {response.json()}")
            return pd.DataFrame()

        data = response.json().get('response', {}).get('data', [])
        return pd.DataFrame(data)

    except requests.exceptions.RequestException as e:
        print(f"Connection error fetching {year}: {e}")
        return pd.DataFrame()

def process_and_export_emissions():
    """
    Loops through target years (2024 to present), computes annual CO2 mass 
    and total MWh by state, calculates grid carbon intensity (lbs CO2 / MWh),
    and exports a single master CSV.
    """
    if not API_KEY:
        print("Error: EIA_API_KEY not found. Please check your .env file.")
        return

    years = [2024, 2025, 2026]
    all_year_frames = []

    for yr in years:
        df_year = fetch_year_data(API_KEY, yr)
        if not df_year.empty:
            all_year_frames.append(df_year)

    if not all_year_frames:
        print("No data extracted.")
        return

    # Combine multi-year data into a single DataFrame
    raw_df = pd.concat(all_year_frames, ignore_index=True)
    raw_df['year'] = raw_df['period'].str.slice(0, 4)

    # 1. Filter out double-counted rows (use 'ALL' prime mover records or exclude 'ALL' total fuel summaries)
    # Filter for primeMover == 'ALL' to get the single overarching total per fuel type
    df_filtered = raw_df[raw_df['primeMover'] == 'ALL'].copy()
    
    # Exclude the 'ALL' fuel row so we don't double-count total fuel consumption
    df_filtered = df_filtered[df_filtered['fuelType'] != 'ALL']

    # 2. Clean numeric columns
    df_filtered['generation'] = pd.to_numeric(df_filtered['generation'], errors='coerce').fillna(0)
    df_filtered['total-consumption-btu'] = pd.to_numeric(df_filtered['total-consumption-btu'], errors='coerce').fillna(0)

    # 3. Map EPA Carbon Factors using 'fuelType'
    df_filtered['co2_factor'] = df_filtered['fuelType'].map(FUEL_EMISSION_FACTORS).fillna(0.0)
    df_filtered['co2_lbs'] = df_filtered['total-consumption-btu'] * df_filtered['co2_factor']

    # 4. Aggregate by State and Year
    annual_summary = df_filtered.groupby(['state', 'year']).agg(
        annual_mwh=('generation', 'sum'),
        annual_co2_lbs=('co2_lbs', 'sum')
    ).reset_index()

    # 5. Calculate Grid Intensity (lbs CO2 / MWh)
    annual_summary['grid_lbs_co2_per_mwh'] = annual_summary.apply(
        lambda row: row['annual_co2_lbs'] / row['annual_mwh'] if row['annual_mwh'] > 0 else 0,
        axis=1
    )

    # 6. Write to CSV
    os.makedirs("Data", exist_ok=True)
    output_path = "Data/state_grid_carbon_intensity_2024_present.csv"
    annual_summary.to_csv(output_path, index=False)

    print("\nProcessing Complete!")
    print(f"Master CSV written to: {output_path}")
    print("\nSample Preview:")
    print(annual_summary.head(10))

if __name__ == "__main__":
    process_and_export_emissions()