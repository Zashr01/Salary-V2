import streamlit as st
import json
import os
import requests
import uuid
import time
import extra_streamlit_components as stx

# --- Configuration & Constants ---
DEFAULT_VALUES = {
    "exchange_rate": 1.0,
    "normal_rate": 120.0,
    "ot_rate": 300.0,
    "super_ot_rate": 420.0,
    "per_diem_euro_mult": 4.0,
    "per_diem_other_mult": 3.5,
    "withdrawal_currency": "USD",
    "cathay_rate": 31.6,
    "superrich_rate_usd": 34.0,
    "superrich_rate_twd": 1.05,
    "transport_rate": 700.0,
    "bh_hours": 89,
    "bh_mins": 38,
    "p1_hours": 175,
    "p1_mins": 43,
    "p2_hours": 158,
    "p2_mins": 37,
    "base_salary": 16000.0,
    "position_allowance": 1000.0,
    "transport_trips": 6
}

USER_DATA_DIR = "user_data"
if not os.path.exists(USER_DATA_DIR):
    os.makedirs(USER_DATA_DIR)

# --- Page Config ---
st.set_page_config(page_title="Salary App (Pro)", page_icon="💰", layout="wide")

# --- Cookie Manager ---
def get_manager():
    return stx.CookieManager()

cookie_manager = get_manager()

# --- Persistence Helpers ---
def get_user_file(user_id):
    return os.path.join(USER_DATA_DIR, f"user_{user_id}.json")

def load_data_from_file(user_id):
    filepath = get_user_file(user_id)
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            return data
        except:
            return DEFAULT_VALUES.copy()
    return DEFAULT_VALUES.copy()

def save_data_to_file(user_id, data):
    filepath = get_user_file(user_id)
    try:
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        st.error(f"Save Error: {e}")

# --- Initialize Session State ---
# We use a placeholder to wait for cookie
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
if "data" not in st.session_state:
    st.session_state["data"] = DEFAULT_VALUES.copy()

# --- Cookie Logic ---
# Get all cookies
cookies = cookie_manager.get_all()
# Check for existing device_id
device_id = cookies.get("device_id")

if not device_id:
    # New User: Generate ID and Set Cookie
    new_id = str(uuid.uuid4())
    cookie_manager.set("device_id", new_id, expires_at=None) # No expiry = persistent
    # Wait for reload (Streamlit quirk: cookie set needs rerun to be visible next time)
    # But we can proceed using new_id in memory for now
    st.session_state["user_id"] = new_id
    # No file yet, use default
else:
    # Existing User
    if st.session_state["user_id"] != device_id:
        st.session_state["user_id"] = device_id
        # Load data immediately
        st.session_state["data"] = load_data_from_file(device_id)

# --- Helper to get values ---
def val(key):
    return st.session_state["data"].get(key, DEFAULT_VALUES[key])

# --- Auto Save Handler ---
def on_change_handler():
    # Sync widgets to state
    for key in DEFAULT_VALUES.keys():
        if key in st.session_state:
             st.session_state["data"][key] = st.session_state[key]
    
    # Save to file using user_id
    if st.session_state["user_id"]:
        save_data_to_file(st.session_state["user_id"], st.session_state["data"])

# --- UI ---
st.title("💰 Salary App (Pro)")

# Sidebar (Simplified)
with st.sidebar:
    st.title("⚙️ Settings")
    st.caption(f"Device ID: {st.session_state['user_id'][:8] if st.session_state['user_id'] else 'Loading...'}")
    
    if st.button("Update Exchange Rates"):
        try:
            resp = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5)
            data = resp.json()
            if data["result"] == "success":
                rates = data["rates"]
                usd_thb = rates.get("THB", 0)
                usd_twd = rates.get("TWD", 0)
                if usd_thb and usd_twd:
                    st.session_state["data"]["superrich_rate_usd"] = usd_thb
                    st.session_state["data"]["cathay_rate"] = usd_twd
                    st.session_state["data"]["superrich_rate_twd"] = usd_thb / usd_twd
                    on_change_handler()
                    st.toast("Rates Updated!", icon="🔄")
                    st.rerun()
        except:
            st.error("API Error")

# Layout
col1, col2 = st.columns([1, 1])

# We wrap inputs in check to ensure user_id is ready (though we handled it above)
if st.session_state["user_id"]:
    with col1:
        st.subheader("⏱️ Time Inputs")
        with st.container(border=True):
            c1, c2 = st.columns(2)
            bh_hours = c1.number_input("BH Hours", value=val("bh_hours"), key="bh_hours", on_change=on_change_handler)
            bh_mins = c2.number_input("BH Mins", value=val("bh_mins"), key="bh_mins", on_change=on_change_handler)
            
            c3, c4 = st.columns(2)
            p1_hours = c3.number_input("EUR.AME.AUS (Hrs)", value=val("p1_hours"), key="p1_hours", on_change=on_change_handler)
            p1_mins = c4.number_input("Mins", value=val("p1_mins"), key="p1_mins", on_change=on_change_handler)
            
            c5, c6 = st.columns(2)
            p2_hours = c5.number_input("Other Regions (Hrs)", value=val("p2_hours"), key="p2_hours", on_change=on_change_handler)
            p2_mins = c6.number_input("Mins", value=val("p2_mins"), key="p2_mins", on_change=on_change_handler)

        st.subheader("💵 Rates & Config")
        with st.container(border=True):
            c7, c8 = st.columns(2)
            base_salary = c7.number_input("Base Salary", value=val("base_salary"), key="base_salary", on_change=on_change_handler)
            pos_allowance = c8.number_input("Position Allow.", value=val("position_allowance"), key="position_allowance", on_change=on_change_handler)
            
            st.divider()
            c9, c10 = st.columns(2)
            normal_rate = c9.number_input("Normal Rate", value=val("normal_rate"), key="normal_rate", on_change=on_change_handler)
            transport_rate = c10.number_input("Transport Rate", value=val("transport_rate"), key="transport_rate", on_change=on_change_handler)
            
            c11, c12 = st.columns(2)
            c11.text_input("OT Rate (2.5x)", value=f"{normal_rate * 2.5:.2f}", disabled=True)
            c12.text_input("Super OT (3.5x)", value=f"{normal_rate * 3.5:.2f}", disabled=True)
            
            st.divider()
            c13, c14 = st.columns(2)
            euro_mult = c13.number_input("Per Diem (Euro Mult)", value=val("per_diem_euro_mult"), key="per_diem_euro_mult", on_change=on_change_handler)
            other_mult = c14.number_input("Per Diem (Other Mult)", value=val("per_diem_other_mult"), key="per_diem_other_mult", on_change=on_change_handler)

    with col2:
        st.subheader("💱 Exchange Settings")
        with st.container(border=True):
            currency_opts = ["USD", "TWD"]
            curr_idx = 0 if val("withdrawal_currency") == "USD" else 1
            withdraw_currency = st.selectbox("Withdrawal Currency", currency_opts, index=curr_idx, key="withdrawal_currency", on_change=on_change_handler)
            
            c15, c16 = st.columns(2)
            cathay_rate = c15.number_input("Cathay Rate (USD->TWD)", value=val("cathay_rate"), key="cathay_rate", on_change=on_change_handler)
            transport_trips = c16.number_input("Transport Trips", value=val("transport_trips"), key="transport_trips", on_change=on_change_handler)
            
            c17, c18 = st.columns(2)
            superrich_usd = c17.number_input("SuperRich (USD->THB)", value=val("superrich_rate_usd"), key="superrich_rate_usd", on_change=on_change_handler)
            superrich_twd = c18.number_input("SuperRich (TWD->THB)", value=val("superrich_rate_twd"), key="superrich_rate_twd", on_change=on_change_handler)

        st.subheader("📊 Calculation Results")
        
        # Logic
        bh_hours = st.session_state["data"]["bh_hours"]
        bh_mins = st.session_state["data"]["bh_mins"]
        total_bh = bh_hours + (bh_mins / 60.0)
        bh_normal_hrs = min(total_bh, 70)
        bh_ot_hrs = max(min(total_bh - 70, 10), 0)
        bh_super_ot_hrs = max(total_bh - 80, 0)
        
        income_normal = bh_normal_hrs * normal_rate
        income_ot = bh_ot_hrs * (normal_rate * 2.5)
        income_super_ot = bh_super_ot_hrs * (normal_rate * 3.5)
        total_bh_income = income_normal + income_ot + income_super_ot
        
        # Per Diem
        p1_total = p1_hours + (p1_mins / 60.0)
        p2_total = p2_hours + (p2_mins / 60.0)
        holding_amount = (euro_mult * p1_total) + (other_mult * p2_total)
        
        if withdraw_currency == "TWD":
            per_diem_thb = (holding_amount * cathay_rate) * superrich_twd
        else:
            per_diem_thb = holding_amount * superrich_usd
            
        transport_income = transport_trips * transport_rate
        grand_total_thb = total_bh_income + per_diem_thb + base_salary + pos_allowance + transport_income
        
        # Display
        with st.container(border=True):
            st.markdown(f"### Total: :green[{grand_total_thb:,.2f} THB]")
            st.markdown(f"**Block Hours Income:** {total_bh_income:,.2f}")
            st.markdown(f"**Per Diem ({withdraw_currency}):** {holding_amount:,.2f}")
            st.markdown(f"**Per Diem (THB):** {per_diem_thb:,.2f}")
            st.markdown(f"**Base + Allowance:** {base_salary + pos_allowance:,.2f}")
            st.markdown(f"**Transport:** {transport_income:,.2f}")
else:
    st.info("Loading Profile...")
