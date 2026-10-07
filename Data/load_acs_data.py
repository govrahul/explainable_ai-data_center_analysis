"""
Download ACS 5-Year socioeconomic data for every U.S. census tract.

Source:
    U.S. Census Bureau
    American Community Survey 5-Year Estimates

Geography:
    Census tract

Output:
    acs_tract_socioeconomic_2024.csv

Requires:
    pip install requests pandas
"""

import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv


# ============================================================
# CONFIGURATION
# ============================================================

YEAR = 2024

load_dotenv('.env')
API_KEY = os.getenv("CENSUS_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "CENSUS_API_KEY environment variable not found.\n"
        "Set it before running the script."
    )


BASE_URL = (
    f"https://api.census.gov/data/"
    f"{YEAR}/acs/acs5"
)


# All 50 states + DC.
# Puerto Rico is intentionally excluded for a U.S. states/DC analysis.
STATE_FIPS = {
    "01": "AL",
    "02": "AK",
    "04": "AZ",
    "05": "AR",
    "06": "CA",
    "08": "CO",
    "09": "CT",
    "10": "DE",
    "11": "DC",
    "12": "FL",
    "13": "GA",
    "15": "HI",
    "16": "ID",
    "17": "IL",
    "18": "IN",
    "19": "IA",
    "20": "KS",
    "21": "KY",
    "22": "LA",
    "23": "ME",
    "24": "MD",
    "25": "MA",
    "26": "MI",
    "27": "MN",
    "28": "MS",
    "29": "MO",
    "30": "MT",
    "31": "NE",
    "32": "NV",
    "33": "NH",
    "34": "NJ",
    "35": "NM",
    "36": "NY",
    "37": "NC",
    "38": "ND",
    "39": "OH",
    "40": "OK",
    "41": "OR",
    "42": "PA",
    "44": "RI",
    "45": "SC",
    "46": "SD",
    "47": "TN",
    "48": "TX",
    "49": "UT",
    "50": "VT",
    "51": "VA",
    "53": "WA",
    "54": "WV",
    "55": "WI",
    "56": "WY",
}


# ============================================================
# ACS VARIABLES
# ============================================================

VARIABLES = {
    # Population
    "B01003_001E": "population",

    # Income
    "B19013_001E": "median_household_income",

    # Poverty
    "B17001_001E": "poverty_universe",
    "B17001_002E": "poverty_below",

    # Employment
    "B23025_001E": "labor_force",
    "B23025_005E": "unemployed",

    # Education
    "B15003_001E": "education_universe",
    "B15003_022E": "bachelors",

    # Race
    "B02001_001E": "race_total",
    "B02001_003E": "black_alone",

    # Hispanic / Latino
    "B03003_001E": "hispanic_total",
    "B03003_003E": "hispanic",

    # Housing
    "B25070_001E": "rent_universe",

    "B25070_007E": "rent_30_34_pct",
    "B25070_008E": "rent_35_39_pct",
    "B25070_009E": "rent_40_49_pct",
    "B25070_010E": "rent_50_plus_pct",
}


# ============================================================
# DOWNLOAD FUNCTION
# ============================================================

def download_state(state_fips, state_abbr):
    """
    Download all census tracts for one state.
    """

    variable_string = ",".join(
        ["NAME"] + list(VARIABLES.keys())
    )

    params = {
        "get": variable_string,

        # All tracts in this state
        "for": "tract:*",

        # Restrict to state
        "in": f"state:{state_fips}",

        "key": API_KEY,
    }

    print(
        f"Downloading {state_abbr} "
        f"(FIPS {state_fips})..."
    )

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    # First row contains column names
    columns = data[0]

    df = pd.DataFrame(
        data[1:],
        columns=columns
    )

    # Rename ACS variables
    rename_dict = {
        variable: name
        for variable, name in VARIABLES.items()
    }

    df = df.rename(
        columns=rename_dict
    )

    # Create useful FIPS fields
    df["state_fips"] = df["state"].str.zfill(2)
    df["county_fips"] = (
        df["state"].str.zfill(2)
        + df["county"].str.zfill(3)
    )

    df["tract_fips"] = (
        df["state"].str.zfill(2)
        + df["county"].str.zfill(3)
        + df["tract"].str.zfill(6)
    )

    df["state_abbr"] = state_abbr

    return df


# ============================================================
# CALCULATE SOCIOECONOMIC METRICS
# ============================================================

def calculate_metrics(df):

    numeric_columns = [
        column
        for column in df.columns
        if column not in [
            "NAME",
            "state",
            "county",
            "tract",
            "state_fips",
            "county_fips",
            "tract_fips",
            "state_abbr",
        ]
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # --------------------------------------------------------
    # Poverty rate
    # --------------------------------------------------------

    df["poverty_pct"] = (
        df["poverty_below"]
        / df["poverty_universe"]
        * 100
    )

    # --------------------------------------------------------
    # Unemployment rate
    # --------------------------------------------------------

    df["unemployment_pct"] = (
        df["unemployed"]
        / df["labor_force"]
        * 100
    )

    # --------------------------------------------------------
    # Bachelor's degree or higher
    # --------------------------------------------------------

    df["bachelors_pct"] = (
        df["bachelors"]
        / df["education_universe"]
        * 100
    )

    # --------------------------------------------------------
    # Black population
    # --------------------------------------------------------

    df["black_pct"] = (
        df["black_alone"]
        / df["race_total"]
        * 100
    )

    # --------------------------------------------------------
    # Hispanic / Latino population
    # --------------------------------------------------------

    df["hispanic_pct"] = (
        df["hispanic"]
        / df["hispanic_total"]
        * 100
    )

    # --------------------------------------------------------
    # Severe rent burden
    #
    # ACS B25070 categories:
    # 30-34.9%
    # 35-39.9%
    # 40-49.9%
    # 50%+
    # --------------------------------------------------------

    df["rent_burden_30_plus"] = (
        df[
            [
                "rent_30_34_pct",
                "rent_35_39_pct",
                "rent_40_49_pct",
                "rent_50_plus_pct",
            ]
        ]
        .sum(axis=1)
    )

    # --------------------------------------------------------
    # 40%+ rent burden
    # --------------------------------------------------------

    df["rent_burden_40_plus"] = (
        df[
            [
                "rent_40_49_pct",
                "rent_50_plus_pct",
            ]
        ]
        .sum(axis=1)
    )

    # --------------------------------------------------------
    # Clean infinite values
    # --------------------------------------------------------

    df = df.replace(
        [float("inf"), float("-inf")],
        pd.NA
    )

    return df


# ============================================================
# MAIN
# ============================================================

def main():

    all_states = []

    total_states = len(STATE_FIPS)

    for i, (state_fips, state_abbr) in enumerate(
        STATE_FIPS.items(),
        start=1
    ):

        print(
            f"[{i}/{total_states}] ",
            end=""
        )

        try:

            df = download_state(
                state_fips,
                state_abbr
            )

            print(
                f"    {len(df):,} census tracts"
            )

            all_states.append(df)

        except Exception as e:

            print(
                f"    ERROR: {e}"
            )

        # Be polite to the API
        time.sleep(0.25)


    # --------------------------------------------------------
    # Combine states
    # --------------------------------------------------------

    if not all_states:
        raise RuntimeError(
            "No ACS data were downloaded."
        )

    df = pd.concat(
        all_states,
        ignore_index=True
    )


    # --------------------------------------------------------
    # Calculate derived metrics
    # --------------------------------------------------------

    df = calculate_metrics(df)


    # --------------------------------------------------------
    # Add ACS vintage
    # --------------------------------------------------------

    df["acs_year"] = YEAR


    # --------------------------------------------------------
    # Select final columns
    # --------------------------------------------------------

    final_columns = [

        # Geography
        "tract_fips",
        "county_fips",
        "state_fips",
        "state_abbr",
        "NAME",

        # ACS vintage
        "acs_year",

        # Population
        "population",

        # Income
        "median_household_income",

        # Poverty
        "poverty_universe",
        "poverty_below",
        "poverty_pct",

        # Employment
        "labor_force",
        "unemployed",
        "unemployment_pct",

        # Education
        "education_universe",
        "bachelors",
        "bachelors_pct",

        # Race
        "race_total",
        "black_alone",
        "black_pct",

        # Hispanic
        "hispanic_total",
        "hispanic",
        "hispanic_pct",

        # Housing
        "rent_universe",
        "rent_burden_30_plus",
        "rent_burden_40_plus",
    ]


    df = df[
        [
            column
            for column in final_columns
            if column in df.columns
        ]
    ]


    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    output_file = (
        f"Data/acs_tract_socioeconomic_{YEAR}.csv"
    )

    df.to_csv(
        output_file,
        index=False
    )


    # --------------------------------------------------------
    # Also save Parquet
    # --------------------------------------------------------

    parquet_file = (
        f"acs_tract_socioeconomic_{YEAR}.parquet"
    )

    try:

        df.to_parquet(
            parquet_file,
            index=False
        )

        parquet_message = (
            f"Saved {parquet_file}"
        )

    except Exception as e:

        parquet_message = (
            f"Could not save Parquet: {e}"
        )


    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("DOWNLOAD COMPLETE")
    print("=" * 60)

    print(
        f"Census tracts: {len(df):,}"
    )

    print(
        f"States/DC: {df['state_fips'].nunique()}"
    )

    print(
        f"CSV: {output_file}"
    )

    print(
        parquet_message
    )

    print("\nColumns:")
    for column in df.columns:
        print(f"  {column}")


if __name__ == "__main__":
    main()