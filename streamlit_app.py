import json
from datetime import datetime, date

import httpx
import streamlit as st

BASE_URL_DEFAULT = "http://127.0.0.1:8000"


def call_api(method: str, path: str, json_body=None, params=None):
    try:
        with httpx.Client(timeout=15.0) as client:
            url = f"{st.session_state.base_url.rstrip('/')}{path}"
            response = client.request(method, url, json=json_body, params=params)
        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            return response.text
    except Exception as exc:
        return {"error": str(exc)}


def show_response(resp):
    if isinstance(resp, dict) or isinstance(resp, list):
        st.json(resp)
    else:
        st.text(str(resp))


st.set_page_config(page_title="Fleet Management UI", layout="wide")
st.title("Fleet Management Streamlit UI")

if "base_url" not in st.session_state:
    st.session_state.base_url = BASE_URL_DEFAULT

with st.sidebar:
    st.header("API Settings")
    st.session_state.base_url = st.text_input("Backend URL", value=st.session_state.base_url)
    st.markdown("---")
    st.write("Use this UI to call the FastAPI backend endpoints.")
    st.write("Make sure the backend is running on the selected URL.")

st.header("Quick checks")
col1, col2 = st.columns(2)
with col1:
    if st.button("Health check"):
        resp = call_api("GET", "/")
        show_response(resp)
with col2:
    if st.button("Redis status"):
        resp = call_api("GET", "/redis-status")
        show_response(resp)

st.markdown("---")

st.header("GPS update")
with st.form("gps_form"):
    tenant_id = st.number_input("Tenant ID", min_value=1, value=1)
    vehicle_id = st.number_input("Vehicle ID", min_value=1, value=1)
    latitude = st.number_input("Latitude", value=27.700769)
    longitude = st.number_input("Longitude", value=85.300140)
    heading = st.number_input("Heading", min_value=0, max_value=359, value=0)
    speed_kmh = st.number_input("Speed (km/h)", min_value=0.0, value=0.0)
    battery_pct = st.number_input("Battery %", min_value=0, max_value=100, value=100)
    recorded_at = st.text_input("Recorded at (ISO)", value=datetime.now().isoformat())
    submitted = st.form_submit_button("Send GPS update")
    if submitted:
        payload = {
            "tenant_id": tenant_id,
            "vehicle_id": vehicle_id,
            "latitude": str(latitude),
            "longitude": str(longitude),
            "heading": heading,
            "speed_kmh": str(speed_kmh),
            "battery_pct": battery_pct,
            "recorded_at": recorded_at,
        }
        resp = call_api("POST", "/gps", json_body=payload)
        show_response(resp)

st.markdown("---")

st.header("Create daily log sheet")
with st.form("daily_log_form"):
    tenant_id = st.number_input("Tenant ID", min_value=1, value=1, key="dlt_tenant")
    vehicle_id = st.number_input("Vehicle ID", min_value=1, value=1, key="dlt_vehicle")
    driver_id = st.number_input("Driver ID", min_value=0, value=1, key="dlt_driver")
    conductor_id = st.number_input("Conductor ID", min_value=0, value=1, key="dlt_conductor")
    date_gregorian = st.date_input("Date", value=date.today(), key="dlt_date")
    start_km = st.number_input("Start KM", value=0.0, key="dlt_start")
    end_km = st.number_input("End KM", value=0.0, key="dlt_end")
    start_charging_pct = st.number_input("Start charge %", min_value=0, max_value=100, value=100, key="dlt_start_charge")
    end_charging_pct = st.number_input("End charge %", min_value=0, max_value=100, value=100, key="dlt_end_charge")
    trip_count = st.number_input("Trip count", min_value=0, value=0, key="dlt_trip_count")
    cash_collected = st.number_input("Cash collected", value=0.0, key="dlt_cash")
    qr_collected = st.number_input("QR collected", value=0.0, key="dlt_qr")
    remarks = st.text_area("Remarks", key="dlt_remarks")
    submitted = st.form_submit_button("Create daily log sheet")
    if submitted:
        payload = {
            "tenant_id": tenant_id,
            "vehicle_id": vehicle_id,
            "driver_id": driver_id or None,
            "conductor_id": conductor_id or None,
            "date_gregorian": date_gregorian.isoformat(),
            "start_km": str(start_km),
            "end_km": str(end_km),
            "start_charging_pct": start_charging_pct,
            "end_charging_pct": end_charging_pct,
            "trip_count": trip_count,
            "cash_collected": str(cash_collected),
            "qr_collected": str(qr_collected),
            "remarks": remarks or None,
        }
        resp = call_api("POST", "/daily-log-sheets", json_body=payload)
        show_response(resp)

st.markdown("---")

st.header("Owner share query")
with st.form("owner_share_form"):
    vehicle_id = st.number_input("Vehicle ID", min_value=1, value=1, key="os_vehicle")
    query_date = st.date_input("Date", value=date.today(), key="os_date")
    submitted = st.form_submit_button("Get owner share")
    if submitted:
        params = {"date_gregorian": query_date.isoformat()}
        resp = call_api("GET", f"/daily-log-sheets/{vehicle_id}/owner-share", params=params)
        show_response(resp)

st.markdown("---")

st.header("Run reconciliation")
with st.form("reconciliation_form"):
    tenant_id = st.number_input("Tenant ID", min_value=1, value=1, key="rec_tenant")
    submitted = st.form_submit_button("Run reconciliation")
    if submitted:
        resp = call_api("POST", "/reconciliation/run", json_body={"tenant_id": tenant_id})
        show_response(resp)

st.markdown("---")

st.write("If the backend is not running, start it with `python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000`.")
