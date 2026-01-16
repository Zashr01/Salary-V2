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
st.set_page_config(page_title="EVA Air Income Calculator", page_icon="✈️", layout="wide")

# --- PWA & Mobile Optimization ---
st.markdown("""
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="EVA Income">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
""", unsafe_allow_html=True)

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
        # Silently fail or log, but don't disrupt user
        pass

# --- Initialize Session State ---
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
if "data" not in st.session_state:
    st.session_state["data"] = DEFAULT_VALUES.copy()

import datetime

# --- Cookie Logic ---
# Add Exception Handling for Cookie Manager
try:
    cookies = cookie_manager.get_all()
    device_id = cookies.get("device_id") if cookies else None
except:
    device_id = None

if not device_id:
    try:
        # New User
        new_id = str(uuid.uuid4())
        # Expires in 365 days
        expire_date = datetime.datetime.now() + datetime.timedelta(days=365)
        cookie_manager.set("device_id", new_id, expires_at=expire_date)
        st.session_state["user_id"] = new_id
        time.sleep(0.1)
        st.rerun()
    except:
        # Fallback if cookies disabled
        pass
else:
    # Existing User
    if st.session_state["user_id"] != device_id:
        st.session_state["user_id"] = device_id
        st.session_state["data"] = load_data_from_file(device_id)

# --- Helper to get values ---
def val(key):
    v = st.session_state["data"].get(key, DEFAULT_VALUES[key])
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return float(v)
    return v

# --- Auto Save Handler ---
def on_change_handler():
    # Sync widgets to state
    for key in DEFAULT_VALUES.keys():
        if key in st.session_state:
             st.session_state["data"][key] = st.session_state[key]
    
    # Save to file
    if st.session_state["user_id"]:
        save_data_to_file(st.session_state["user_id"], st.session_state["data"])

# --- Main UI ---
st.title("✈️ EVA Air Income Calculator")

if st.session_state["user_id"]:
    # 1. CALCULATE FIRST
    bh_hours = val("bh_hours")
    bh_mins = val("bh_mins")
    total_bh = bh_hours + (bh_mins / 60.0)
    bh_normal_hrs = min(total_bh, 70)
    bh_ot_hrs = max(min(total_bh - 70, 10), 0)
    bh_super_ot_hrs = max(total_bh - 80, 0)
    
    normal_rate = val("normal_rate")
    income_normal = bh_normal_hrs * normal_rate
    income_ot = bh_ot_hrs * (normal_rate * 2.5)
    income_super_ot = bh_super_ot_hrs * (normal_rate * 3.5)
    total_bh_income = income_normal + income_ot + income_super_ot
    
    p1_hours = val("p1_hours")
    p1_mins = val("p1_mins")
    p2_hours = val("p2_hours")
    p2_mins = val("p2_mins")
    euro_mult = val("per_diem_euro_mult")
    other_mult = val("per_diem_other_mult")
    
    p1_total = p1_hours + (p1_mins / 60.0)
    p2_total = p2_hours + (p2_mins / 60.0)
    holding_amount = (euro_mult * p1_total) + (other_mult * p2_total)
    
    withdraw_currency = val("withdrawal_currency")
    cathay_rate = val("cathay_rate")
    superrich_usd = val("superrich_rate_usd")
    superrich_twd = val("superrich_rate_twd")
    
    if withdraw_currency == "TWD":
        per_diem_thb = (holding_amount * cathay_rate) * superrich_twd
    else:
        per_diem_thb = holding_amount * superrich_usd
        
    base_salary = val("base_salary")
    pos_allowance = val("position_allowance")
    transport_trips = val("transport_trips")
    transport_rate = val("transport_rate")
    transport_income = transport_trips * transport_rate
    grand_total_thb = total_bh_income + per_diem_thb + base_salary + pos_allowance + transport_income


    # 2. HERO SECTION (Results at Top)
    # ------------------------------------------------
    st.markdown(f"""
    <div style="background-color: #2e7d32; padding: 20px; border-radius: 10px; text-align: center; color: white; margin-bottom: 20px;">
        <h2 style="margin:0; color: white;">Total Estimated Income</h2>
        <h1 style="margin:0; font-size: 3em; color: white;">{grand_total_thb:,.2f} THB</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Breakdown Metrics (Row)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Block Hours Income", f"{total_bh_income:,.0f}")
    m2.metric(f"Per Diem ({withdraw_currency})", f"{holding_amount:,.0f}")
    m3.metric("Per Diem (THB)", f"{per_diem_thb:,.0f}")
    m4.metric("Base + Allowance", f"{base_salary + pos_allowance:,.0f}")

    st.divider()

    # 3. INPUT SECTIONS (Using number_input for numeric keyboard)
    # ------------------------------------------------
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("⏱️ Time Inputs")
        with st.container(border=True):
            c1, c2 = st.columns(2)
            # step=1.0 ensures integer-like increment but keeps it float friendly. 
            # format="%d" or "%f" controls display. Let's use flexible format.
            st.number_input("BH Hours", value=val("bh_hours"), key="bh_hours", on_change=on_change_handler, step=1.0)
            st.number_input("BH Mins", value=val("bh_mins"), key="bh_mins", on_change=on_change_handler, step=1.0)
            
            c3, c4 = st.columns(2)
            st.number_input("EUR.AME.AUS (Hrs)", value=val("p1_hours"), key="p1_hours", on_change=on_change_handler, step=1.0)
            st.number_input("Mins", value=val("p1_mins"), key="p1_mins", on_change=on_change_handler, step=1.0)
            
            c5, c6 = st.columns(2)
            st.number_input("Other Regions (Hrs)", value=val("p2_hours"), key="p2_hours", on_change=on_change_handler, step=1.0)
            st.number_input("Mins", value=val("p2_mins"), key="p2_mins", on_change=on_change_handler, step=1.0)

        st.subheader("💵 Rates & Config")
        with st.container(border=True):
            c7, c8 = st.columns(2)
            st.number_input("Base Salary", value=val("base_salary"), key="base_salary", on_change=on_change_handler, step=100.0)
            st.number_input("Position Allow.", value=val("position_allowance"), key="position_allowance", on_change=on_change_handler, step=100.0)
            
            st.divider()
            c9, c10 = st.columns(2)
            st.number_input("Normal Rate", value=val("normal_rate"), key="normal_rate", on_change=on_change_handler, step=10.0)
            st.number_input("Transport Rate", value=val("transport_rate"), key="transport_rate", on_change=on_change_handler, step=50.0)
            
            c11, c12 = st.columns(2)
            st.text_input("OT Rate (2.5x)", value=f"{normal_rate * 2.5:.2f}", disabled=True)
            st.text_input("Super OT (3.5x)", value=f"{normal_rate * 3.5:.2f}", disabled=True)
            
            st.divider()
            c13, c14 = st.columns(2)
            st.number_input("Per Diem (Euro Mult)", value=val("per_diem_euro_mult"), key="per_diem_euro_mult", on_change=on_change_handler, step=0.5)
            st.number_input("Per Diem (Other Mult)", value=val("per_diem_other_mult"), key="per_diem_other_mult", on_change=on_change_handler, step=0.5)

    with col2:
        st.subheader("💱 Exchange Settings")
        with st.container(border=True):
            currency_opts = ["USD", "TWD"]
            curr_idx = 0 if val("withdrawal_currency") == "USD" else 1
            st.selectbox("Withdrawal Currency", currency_opts, index=curr_idx, key="withdrawal_currency", on_change=on_change_handler)
            
            c15, c16 = st.columns(2)
            st.number_input("Cathay Rate (USD->TWD)", value=val("cathay_rate"), key="cathay_rate", on_change=on_change_handler, step=0.1, format="%.2f")
            st.number_input("Transport Trips", value=val("transport_trips"), key="transport_trips", on_change=on_change_handler, step=1.0)
            
            c17, c18 = st.columns(2)
            st.number_input("SuperRich (USD->THB)", value=val("superrich_rate_usd"), key="superrich_rate_usd", on_change=on_change_handler, step=0.1, format="%.2f")
            st.number_input("SuperRich (TWD->THB)", value=val("superrich_rate_twd"), key="superrich_rate_twd", on_change=on_change_handler, step=0.01, format="%.2f")

    # Sidebar Actions
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

else:
    st.info("Initializing Profile...")
