"""Build a one-row-per-facility master dataset from the source CSV files.

County ACS data is fixed at 2024, so grid intensity is joined for 2024 as
well. Drought data is reduced to each county's latest available observation.
All joins preserve facility rows; locations that cannot be matched remain null.
"""

from pathlib import Path
import unicodedata

import pandas as pd


DATA_DIR = Path(__file__).resolve().parent
FACILITIES_FILE = DATA_DIR / "facilities_data.csv"
ACS_FILE = DATA_DIR / "acs_county_socioeconomic_2024.csv"
DROUGHT_FILE = DATA_DIR / "county_drought.csv"
GRID_FILE = DATA_DIR / "state_grid_carbon_intensity_2024_present.csv"
OUTPUT_FILE = DATA_DIR / "master_dataset.csv"
GRID_YEAR = 2024


def _require_columns(
    data: pd.DataFrame, columns: set[str], source_name: str
) -> None:
    missing = columns.difference(data.columns)
    if missing:
        raise ValueError(
            f"{source_name} is missing required columns: {', '.join(sorted(missing))}"
        )


def _county_identity(value: object) -> tuple[str | None, str | None]:
    """Normalize a county name and retain city-vs-county identity."""
    if pd.isna(value):
        return None, None

    name = unicodedata.normalize("NFKD", str(value).casefold())
    name = "".join(char for char in name if not unicodedata.combining(char))
    name = " ".join(name.split())

    if name.endswith(" (independent city)"):
        name = name[: -len(" (independent city)")].strip()
        geography_type = "city"
    else:
        geography_type = None
        suffixes = (
            (" county", "county"),
            (" parish", "county"),
            (" borough", "county"),
            (" census area", "county"),
            (" municipality", "county"),
            (" municipio", "county"),
            (" city", "city"),
        )
        for suffix, kind in suffixes:
            if name.endswith(suffix):
                name = name[: -len(suffix)].strip()
                geography_type = kind
                break

    normalized_name = "".join(char for char in name if char.isalnum())
    if not normalized_name:
        return None, geography_type
    return normalized_name, geography_type


def _build_county_fips_lookup(acs: pd.DataFrame) -> dict[tuple[str, str, str | None], str]:
    """Map unambiguous state/county names to ACS county FIPS codes."""
    candidates: dict[tuple[str, str], list[tuple[str | None, str]]] = {}

    for row in acs.itertuples(index=False):
        state = str(row.state_abbr).strip().upper()
        county_name = str(row.NAME).rsplit(",", maxsplit=1)[0]
        name, geography_type = _county_identity(county_name)
        if name is None:
            continue
        candidates.setdefault((state, name), []).append(
            (geography_type, str(row.county_fips).zfill(5))
        )

    lookup: dict[tuple[str, str, str | None], str] = {}
    for (state, name), entries in candidates.items():
        by_type: dict[str | None, list[str]] = {}
        for geography_type, fips in entries:
            by_type.setdefault(geography_type, []).append(fips)

        for geography_type, fips_codes in by_type.items():
            if len(fips_codes) == 1:
                lookup[(state, name, geography_type)] = fips_codes[0]

        # A facility without a county/city suffix is safe to map only when the
        # name identifies exactly one county-equivalent in that state.
        if len(entries) == 1:
            lookup[(state, name, None)] = entries[0][1]

    return lookup


def build_master_dataset() -> pd.DataFrame:
    """Load, validate, and join the four inputs at facility grain."""
    facilities = pd.read_csv(FACILITIES_FILE, dtype={"location_state": "string"})
    acs = pd.read_csv(ACS_FILE, dtype={"county_fips": "string"})
    drought = pd.read_csv(DROUGHT_FILE, dtype={"fips": "string"})
    grid = pd.read_csv(GRID_FILE, dtype={"state": "string"})

    _require_columns(
        facilities,
        {"id", "location_state", "location_county"},
        FACILITIES_FILE.name,
    )
    _require_columns(
        acs,
        {"county_fips", "state_abbr", "NAME"},
        ACS_FILE.name,
    )
    _require_columns(
        drought,
        {"fips", "mapDate"},
        DROUGHT_FILE.name,
    )
    _require_columns(
        grid,
        {"state", "year"},
        GRID_FILE.name,
    )

    if acs["county_fips"].duplicated().any():
        raise ValueError(f"{ACS_FILE.name} contains duplicate county_fips values")

    acs["county_fips"] = acs["county_fips"].str.zfill(5)
    facilities["_state_key"] = (
        facilities["location_state"].str.strip().str.upper()
    )
    county_lookup = _build_county_fips_lookup(acs)
    facility_counties = facilities["location_county"].map(_county_identity)
    facilities["county_fips"] = [
        county_lookup.get((state or "", name or "", geography_type))
        for state, (name, geography_type) in zip(
            facilities["_state_key"], facility_counties
        )
    ]

    master = facilities.merge(
        acs,
        on="county_fips",
        how="left",
        validate="many_to_one",
    )

    drought["fips"] = drought["fips"].str.zfill(5)
    drought["mapDate"] = pd.to_datetime(drought["mapDate"], errors="raise")
    drought = drought.drop_duplicates()
    if drought.duplicated(["fips", "mapDate"]).any():
        raise ValueError(
            f"{DROUGHT_FILE.name} has conflicting rows for the same county and date"
        )
    latest_drought = (
        drought.sort_values("mapDate")
        .drop_duplicates("fips", keep="last")
        .rename(
            columns={
                column: f"drought_{column}"
                for column in drought.columns
                if column != "fips"
            }
            | {"fips": "county_fips"}
        )
    )
    master = master.merge(
        latest_drought,
        on="county_fips",
        how="left",
        validate="many_to_one",
    )

    grid["state"] = grid["state"].str.strip().str.upper()
    grid["year"] = pd.to_numeric(grid["year"], errors="raise").astype(int)
    selected_grid = grid.loc[grid["year"].eq(GRID_YEAR)].copy()
    if selected_grid.empty:
        raise ValueError(f"{GRID_FILE.name} has no rows for {GRID_YEAR}")
    if selected_grid["state"].duplicated().any():
        raise ValueError(
            f"{GRID_FILE.name} contains duplicate state rows for {GRID_YEAR}"
        )
    selected_grid = selected_grid.rename(
        columns={
            column: column if column.startswith("grid_") else f"grid_{column}"
            for column in selected_grid.columns
            if column != "state"
        }
        | {"state": "_state_key"}
    )
    master = master.merge(
        selected_grid,
        on="_state_key",
        how="left",
        validate="many_to_one",
    )

    master = master.drop(columns="_state_key")
    if len(master) != len(facilities) or master["id"].duplicated().any():
        raise ValueError("Joins changed the facility row count or duplicated IDs")
    return master


def main() -> None:
    master = build_master_dataset()
    master.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved {len(master):,} facilities to {OUTPUT_FILE}")
    print(
        "County ACS matches: "
        f"{master['population'].notna().sum():,}/{len(master):,}"
    )
    print(
        "Latest county drought matches: "
        f"{master['drought_mapDate'].notna().sum():,}/{len(master):,}"
    )
    print(
        f"{GRID_YEAR} state grid matches: "
        f"{master['grid_year'].notna().sum():,}/{len(master):,}"
    )


if __name__ == "__main__":
    main()