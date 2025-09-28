# streamlit_app.py
import streamlit as st
import pandas as pd
import joblib
from datetime import datetime
import matplotlib.pyplot as plt
from strava_api import save_activities_csv
import os
import sklearn
st.write("Running scikit-learn version:", sklearn.__version__)
st.title("🏃 Strava Run Pace Predictor")

# --- Load model and features ---
model = joblib.load("model.pkl")
features = joblib.load("features.pkl")

# --- Load activities ---
if st.button("Refresh Strava Data"):
    df = save_activities_csv()
else:
    if os.path.exists("data/activities.csv"):
        df = pd.read_csv("data/activities.csv")
    else:
        st.warning("No data found. Click 'Refresh Strava Data' to pull activities from Strava.")
        df = pd.DataFrame()

if not df.empty:
    df["date"] = pd.to_datetime(df["start_date"])
    df["distance_km"] = df["distance"] / 1000
    df["elev_gain_m"] = df["total_elevation_gain"]
    df["pace_min_per_km"] = (df["moving_time"] / 60) / df["distance_km"]

    # Fill missing timezones
    df["timezone"] = df["timezone"].fillna("Unknown")
    timezones = df["timezone"].unique().tolist()

    # Compute rolling mileage
    df = df.sort_values("date").set_index("date")
    df["rolling_7d_km"] = df["distance_km"].rolling("7D").sum().fillna(0)
    df["rolling_30d_km"] = df["distance_km"].rolling("30D").sum().fillna(0)
    df = df.reset_index()

    default_7d = df["rolling_7d_km"].iloc[-1] if not df.empty else 0
    default_30d = df["rolling_30d_km"].iloc[-1] if not df.empty else 0

    # --- Sidebar inputs ---
    st.sidebar.header("Plan Your Next Run")
    distance_km = st.sidebar.number_input("Distance (km)", min_value=1.0, max_value=50.0, value=10.0, step=0.5)
    elev_gain_m = st.sidebar.number_input("Elevation Gain (m)", min_value=0, max_value=2000, value=100, step=10)
    rolling_7d_km = st.sidebar.number_input("Last 7 days total km", value=default_7d)
    rolling_30d_km = st.sidebar.number_input("Last 30 days total km", value=default_30d)
    run_time = st.sidebar.time_input("Run Start Time", value=datetime.now().time())
    hour = run_time.hour

    tz = st.sidebar.selectbox("Timezone", timezones)
    tz_code = pd.Categorical([tz], categories=timezones).codes[0]

    # --- Prepare input for model ---
    X_input = pd.DataFrame([{
        "distance_km": distance_km,
        "elev_gain_m": elev_gain_m,
        "rolling_7d_km": rolling_7d_km,
        "rolling_30d_km": rolling_30d_km,
        "hour": hour,
        "timezone_code": tz_code
    }])

    # --- Predict ---
    if st.sidebar.button("Predict Pace"):
        X_input = X_input.reindex(columns=features, fill_value=0)
        pace_pred = model.predict(X_input)[0]
        st.metric("Predicted Pace", f"{pace_pred:.2f} min/km")

    # --- Historical Pace Plot ---
    st.header("📊 Past Run Pace")
    runs = df[df["type"] == "Run"].copy()
    plt.figure(figsize=(10,4))
    plt.plot(runs["date"].to_numpy(), runs["pace_min_per_km"].to_numpy(), marker='o', linestyle='-')
    plt.xlabel("Date")
    plt.ylabel("Pace (min/km)")
    plt.title("Run Pace Over Time")
    st.pyplot(plt)
