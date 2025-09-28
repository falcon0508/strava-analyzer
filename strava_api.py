from dotenv import load_dotenv
import requests
import os
import pandas as pd
import time

load_dotenv()

CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")
TOKEN_URL = "https://www.strava.com/oauth/token"
ACTIVITIES_URL = "https://www.strava.com/api/v3/athlete/activities"

def refresh_access_token():
    resp = requests.post(TOKEN_URL, data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN
    })

    if resp.status_code != 200:
        raise Exception(f"Error refreshing token: {resp.text}")

    tokens = resp.json()
    return tokens["access_token"], tokens["refresh_token"], tokens["expires_at"]

def get_activities(per_page=50, max_pages=5):
    """Download recent activities into a pandas DataFrame."""
    access_token, _, _ = refresh_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    all_acts = []
    for page in range(1, max_pages + 1):
        resp = requests.get(ACTIVITIES_URL, headers=headers, params={"per_page": per_page, "page": page})
        data = resp.json()
        if not data:
            break
        all_acts.extend(data)
        time.sleep(0.2)  # be polite with API rate limits

    # Convert to DataFrame
    df = pd.json_normalize(all_acts)
    return df

def save_activities_csv(filename="data/activities.csv"):
    os.makedirs("data", exist_ok=True)  # create folder if it doesn’t exist
    df = get_activities()
    df.to_csv(filename, index=False)
    print(f"Saved {len(df)} activities to {filename}")
    return df

if __name__ == "__main__":
    df = save_activities_csv()
    print(df[["name", "start_date", "distance", "moving_time", "average_speed"]].head())