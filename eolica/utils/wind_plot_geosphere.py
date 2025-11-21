import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
API_BASE = "https://dataset.api.hub.geosphere.at"
STATION_LIST_URL = f"{API_BASE}/v1/station/historical/klima-v2-1m"
STATION_META_URL = f"{API_BASE}/v1/station/meta"
UPPER_AUSTRIA_CODE = "4"  # Bundesland code for Upper Austria
START_YEAR = 2022
END_YEAR = 2022

# --- HELPER FUNCTIONS ---

def get_upper_austria_stations():
    """Fetches all stations in Upper Austria with metadata (lat/lon)."""
    resp = requests.get(STATION_META_URL)
    resp.raise_for_status()
    stations = resp.json()["data"]
    # Filter for Upper Austria (Oberösterreich, Bundesland code "4")
    ua_stations = [
        s for s in stations
        if s.get("bundesland") == UPPER_AUSTRIA_CODE and s.get("lat") and s.get("lon")
    ]
    return ua_stations

def fetch_monthly_data(station_id, year):
    """Fetches monthly wind data for a given station and year."""
    url = f"{API_BASE}/v1/station/historical/klima-v2-1m/{station_id}?year={year}"
    resp = requests.get(url)
    if resp.status_code != 200:
        return None
    return resp.json().get("data", [])

def wind_direction_from_frequencies(row):
    """Calculates average wind direction (degrees) from directional frequencies."""
    # Cardinal directions and their angles (meteorological convention: from where wind blows)
    directions = {
        "tage_ddn": 0,
        "tage_ddne": 45,
        "tage_dde": 90,
        "tage_ddse": 135,
        "tage_dds": 180,
        "tage_ddsw": 225,
        "tage_ddw": 270,
        "tage_ddnw": 315
    }
    total = 0
    x = 0
    y = 0
    for key, angle in directions.items():
        freq = row.get(key, 0) or 0
        rad = np.deg2rad(angle)
        x += freq * np.cos(rad)
        y += freq * np.sin(rad)
        total += freq
    if total == 0:
        return np.nan
    mean_angle = np.arctan2(y, x)
    mean_deg = (np.rad2deg(mean_angle)) % 360
    return mean_deg

def process_station_data(station, years):
    """Aggregates wind data for a station across specified years."""
    dfs = []
    for year in years:
        data = fetch_monthly_data(station["id"], year)
        if not data:
            continue
        df = pd.DataFrame(data)
        dfs.append(df)
    if not dfs:
        return None
    df = pd.concat(dfs, ignore_index=True)
    # Convert relevant columns to numeric
    cols = ["vv_mittel", "tage_ddn", "tage_ddne", "tage_dde", "tage_ddse",
            "tage_dds", "tage_ddsw", "tage_ddw", "tage_ddnw"]
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    # Calculate annual averages
    avg_speed = df["vv_mittel"].mean()
    # Mean wind direction from frequencies
    freq_means = df[cols[1:]].sum().to_dict()
    avg_dir = wind_direction_from_frequencies(freq_means)
    return {
        "id": station["id"],
        "name": station.get("name"),
        "lat": station["lat"],
        "lon": station["lon"],
        "avg_speed": avg_speed,
        "avg_dir": avg_dir
    }

# --- MAIN SCRIPT ---

def main():
    print("Fetching Upper Austria station metadata...")
    stations = get_upper_austria_stations()
    print(f"Found {len(stations)} stations in Upper Austria.")
    years = list(range(START_YEAR, END_YEAR + 1))
    results = []
    for station in stations:
        print(f"Processing {station['name']} ({station['id']})...")
        data = process_station_data(station, years)
        if data and not np.isnan(data["avg_speed"]) and not np.isnan(data["avg_dir"]):
            results.append(data)
    df_results = pd.DataFrame(results)
    df_results.to_csv("upper_austria_wind_summary.csv", index=False)
    print("Data saved to upper_austria_wind_summary.csv")
    # --- QUIVER PLOT ---
    plt.figure(figsize=(10, 8))
    # Convert wind direction (from) to (to) for quiver (matplotlib uses "to" direction)
    angles = np.deg2rad(270 - df_results["avg_dir"])
    u = df_results["avg_speed"] * np.cos(angles)
    v = df_results["avg_speed"] * np.sin(angles)
    plt.quiver(
        df_results["lon"], df_results["lat"],
        u, v,
        df_results["avg_speed"],
        angles='xy', scale_units='xy', scale=1, cmap='viridis'
    )
    plt.colorbar(label="Average Wind Speed (m/s)")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title("Average Monthly Wind Speed and Direction (Upper Austria Stations)")
    for _, row in df_results.iterrows():
        plt.text(row["lon"], row["lat"], row["name"], fontsize=7, ha='center', va='bottom')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
