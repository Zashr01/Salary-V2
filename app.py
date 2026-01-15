import streamlit as st
import json
import os
import requests
import math

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

# --- Persistence Helpers ---
def get_user_file(username):
    return os.path.join(USER_DATA_DIR, f"user_{username}.json")

def load_user_data(username, pin):
    filepath = get_user_file(username)
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            if data.get("pin") == pin:
                return data.get("data", DEFAULT_VALUES.copy())
            else:
                return None # Wrong PIN
        except:
            return None
    return None # Not found

def create_user_profile(username, pin):
    filepath = get_user_file(username)
    new_data = {
        "pin": pin,
        "data": DEFAULT_VALUES.copy()
    }
    with open(filepath, "w") as f:
        json.dump(new_data, f, indent=4)
    return new_data["data"]

def save_current_data():
    if st.session_state.get("is_logged_in") and st.session_state.get("username"):
        username = st.session_state["username"]
        pin = st.session_state.get("pin") # We need to store PIN in session to save
        
        # Collect current values from session state widgets
        current_data = {}
        for key in DEFAULT_VALUES.keys():
            if key in st.session_state:
                 current_data[key] = st.session_state[key]
        
        save_payload = {
            "pin": pin,
            "data": current_data
        }
        
        filepath = get_user_file(username)
        try:
            with open(filepath, "w") as f:
                json.dump(save_payload, f, indent=4)
            return True
        except Exception as e:
            st.error(f"Save Failed: {e}")
            return False
    return False

# --- Page Config ---
st.set_page_config(page_title="Salary App (Pro)", page_icon="💰", layout="wide")

# --- Session State Init ---
if "data" not in st.session_state:
    st.session_state["data"] = DEFAULT_VALUES.copy()
if "is_logged_in" not in st.session_state:
    st.session_state["is_logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None

# Helper to initialize widget values from state
def val(key):
    return st.session_state["data"].get(key, DEFAULT_VALUES[key])

# --- Sidebar: Login & Actions ---
with st.sidebar:
    st.title("🔐 Profile")
    
    if not st.session_state["is_logged_in"]:
        with st.form("login_form"):
            user_input = st.text_input("Username")
            pin_input = st.text_input("PIN (4 digits)", type="password", max_chars=4)
            submitted = st.form_submit_button("Login / Register")
            
            if submitted:
                if not user_input or not pin_input:
                    st.error("Please enter Username and PIN")
                else:
                    filepath = get_user_file(user_input)
                    if os.path.exists(filepath):
                        # Login
                        loaded_data = load_user_data(user_input, pin_input)
                        if loaded_data:
                            st.session_state["data"] = loaded_data
                            st.session_state["is_logged_in"] = True
                            st.session_state["username"] = user_input
                            st.session_state["pin"] = pin_input
                            st.success(f"Welcome back, {user_input}!")
                            st.rerun()
                        else:
                            st.error("Wrong PIN!")
                    else:
                        # Register
                        new_data = create_user_profile(user_input, pin_input)
                        st.session_state["data"] = new_data
                        st.session_state["is_logged_in"] = True
                        st.session_state["username"] = user_input
                        st.session_state["pin"] = pin_input
                        st.success(f"Profile Created: {user_input}")
                        st.rerun()
    else:
        st.info(f"Logged in as: **{st.session_state['username']}**")
        if st.button("Logout"):
            st.session_state["is_logged_in"] = False
            st.session_state["username"] = None
            st.session_state["data"] = DEFAULT_VALUES.copy()
            st.rerun()
        
        if st.button("Save Changes Manually"):
            if save_current_data():
                st.toast("Data Saved!", icon="✅")

    st.divider()
    
    st.subheader("Cloud Sync")
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
                    st.toast("Rates Updated!", icon="🔄")
                    if st.session_state["is_logged_in"]:
                         save_current_data()
                    st.rerun()
        except Exception as e:
            st.error(f"API Error: {e}")

# --- Main App Logic ---
st.title("💰 Salary App (Pro)")

# Ensure session state is updated when widgets change
def on_change_handler():
    # Sync widget values back to session state 'data' dict
    for key in DEFAULT_VALUES.keys():
        if key in st.session_state:
            st.session_state["data"][key] = st.session_state[key]
    
    # Auto-save logic
    if st.session_state["is_logged_in"]:
        save_current_data()

# Layout
col1, col2 = st.columns([1, 1])

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
