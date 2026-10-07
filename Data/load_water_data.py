import io
import time
from datetime import datetime, timedelta

import pandas as pd
import requests


BASE_URL = "https://usdmdataservices.unl.edu/api"

# US states + DC.
# The Drought Monitor API accepts these abbreviations as the
# `aoi` parameter for CountyStatistics.
STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC"
]


def date_chunks(start_date, end_date, max_days=365):
    """
    Split a date range into chunks no longer than max_days.
    """
    current = start_date

    while current <= end_date:
        chunk_end = min(
            current + timedelta(days=max_days - 1),
            end_date
        )

        yield current, chunk_end

        current = chunk_end + timedelta(days=1)


def download_county_drought(
    start_date,
    end_date,
    output_file="county_drought.csv",
    sleep_seconds=0.25
):
    """
    Download weekly U.S. Drought Monitor county statistics.

    Returns:
        pandas.DataFrame
    """

    all_data = []

    session = requests.Session()

    # Ask the API for JSON.
    headers = {
        "Accept": "application/json",
        "User-Agent": "county-drought-data-project/1.0"
    }

    for state in STATES:

        print(f"\nDownloading {state}...")

        for chunk_start, chunk_end in date_chunks(
            start_date,
            end_date
        ):

            url = (
                f"{BASE_URL}/CountyStatistics/"
                f"GetDroughtSeverityStatisticsByAreaPercent"
            )

            params = {
                "aoi": state,
                "startdate": chunk_start.strftime("%-m/%-d/%Y"),
                "enddate": chunk_end.strftime("%-m/%-d/%Y"),
                "statisticsType": 1
            }

            # Windows does not support %-m / %-d.
            # Replace with portable formatting.
            params["startdate"] = (
                f"{chunk_start.month}/"
                f"{chunk_start.day}/"
                f"{chunk_start.year}"
            )

            params["enddate"] = (
                f"{chunk_end.month}/"
                f"{chunk_end.day}/"
                f"{chunk_end.year}"
            )

            print(
                f"  {params['startdate']} - "
                f"{params['enddate']}"
            )

            try:
                response = session.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=120
                )

                response.raise_for_status()

                # The API normally returns JSON when requested
                # through the Accept header.
                data = response.json()

                if isinstance(data, list):
                    df = pd.DataFrame(data)
                else:
                    df = pd.DataFrame(data)

                if not df.empty:
                    df["state"] = state
                    all_data.append(df)

                print(f"    Retrieved {len(df):,} rows")

            except Exception as e:
                print(
                    f"    ERROR downloading {state} "
                    f"{params['startdate']} - "
                    f"{params['enddate']}: {e}"
                )

            # Be polite to the API.
            time.sleep(sleep_seconds)

    if not all_data:
        raise RuntimeError("No data were downloaded.")

    drought = pd.concat(
        all_data,
        ignore_index=True
    )

    # Save the raw-ish combined result.
    drought.to_csv(
        output_file,
        index=False
    )

    print(
        f"\nSaved {len(drought):,} rows to "
        f"{output_file}"
    )

    return drought


if __name__ == "__main__":

    START_DATE = datetime(2024, 1, 1)
    END_DATE = datetime(2026, 9, 1)

    df = download_county_drought(
        start_date=START_DATE,
        end_date=END_DATE,
        output_file="Data/county_drought.csv"
    )

    print("\nColumns returned by the API:")
    print(df.columns.tolist())

    print("\nFirst five rows:")
    print(df.head())