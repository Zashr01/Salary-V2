import flet as ft
import math
import json
import os
import requests

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

# --- Main App ---
def main(page: ft.Page):
    # 1. Page Config
    page.title = "Salary App (Pro)"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.padding = 0
    page.bgcolor = ft.Colors.GREY_50
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.TEAL, font_family="Roboto")

    # --- State ---
    # Current user session state (in memory)
    current_user = {
        "is_logged_in": False,
        "username": None,
        "data": DEFAULT_VALUES.copy() 
    }
    
    # Store UI component references to update them later
    refs = {}

    # --- Persistence Helpers ---
    def get_user_file(username):
        return os.path.join(USER_DATA_DIR, f"user_{username}.json")

    def save_current_profile():
        if current_user["is_logged_in"] and current_user["username"]:
            filepath = get_user_file(current_user["username"])
            try:
                with open(filepath, "w") as f:
                    # Save both PIN (should be hashed in real app, but plain for now) and Data
                    json.dump(current_user, f, indent=4)
            except Exception as e:
                print(f"Save Error: {e}")

    def get_setting(key):
        return current_user["data"].get(key, DEFAULT_VALUES.get(key))

    def save_setting(key, value):
        current_user["data"][key] = value
        # Auto-save to file if logged in
        if current_user["is_logged_in"]:
            save_current_profile()

    # --- Calculation Logic ---
    txt_result_total = ft.Text("0.00 THB", size=40, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
    txt_breakdown = ft.Column(spacing=2)

    def calculate(e=None):
        try:
            # Helper to safely float
            def val(key):
                if key in refs and refs[key].value:
                     return float(refs[key].value)
                return 0.0

            # Get Values direct from UI or State
            # Note: We update state from UI changes below
            
            p1_hours = val("p1_hours")
            p1_mins = val("p1_mins")
            p2_hours = val("p2_hours")
            p2_mins = val("p2_mins")

            normal_rate = val("normal_rate")
            ot_rate = normal_rate * 2.5
            super_ot_rate = normal_rate * 3.5
            
            # Update read-only fields
            if "ot_rate" in refs: refs["ot_rate"].value = f"{ot_rate:.2f}"
            if "super_ot_rate" in refs: refs["super_ot_rate"].value = f"{super_ot_rate:.2f}"
            
            per_diem_euro_mult = val("per_diem_euro_mult")
            per_diem_other_mult = val("per_diem_other_mult")
            
            base_salary = val("base_salary")
            position_allowance = val("position_allowance")
            
            transport_trips = val("transport_trips")
            transport_rate = val("transport_rate")
            
            cathay_rate = val("cathay_rate")
            
            withdraw_currency = refs["withdrawal_currency"].value
            if withdraw_currency == "USD":
                superrich_rate = val("superrich_rate_usd")
            else:
                superrich_rate = val("superrich_rate_twd")

            # Logic
            bh_hours = val("bh_hours")
            bh_mins = val("bh_mins")
            total_bh = bh_hours + (bh_mins / 60.0)
            bh_normal_hrs = min(total_bh, 70)
            bh_ot_hrs = max(min(total_bh - 70, 10), 0)
            bh_super_ot_hrs = max(total_bh - 80, 0)

            income_normal = bh_normal_hrs * normal_rate
            income_ot = bh_ot_hrs * ot_rate
            income_super_ot = bh_super_ot_hrs * super_ot_rate
            total_bh_income = income_normal + income_ot + income_super_ot

            # Per Diem
            p1_total = p1_hours + (p1_mins / 60.0)
            p2_total = p2_hours + (p2_mins / 60.0)
            holding_amount = (per_diem_euro_mult * p1_total) + (per_diem_other_mult * p2_total)
            
            if withdraw_currency == "TWD":
                 # Logic for TWD conversion if needed, simplified here based on previous code
                 # Previous code: holding (USD units) * cathay -> TWD. Then TWD * superrich -> THB
                 per_diem_thb = (holding_amount * cathay_rate) * superrich_rate
            else:
                 per_diem_thb = holding_amount * superrich_rate

            transport_income = transport_trips * transport_rate
            grand_total_thb = total_bh_income + per_diem_thb + base_salary + position_allowance + transport_income

            # Update UI
            txt_result_total.value = f"{grand_total_thb:,.2f} THB"
            
            def breakdown_row(label, val_str, color=ft.Colors.WHITE):
                return ft.Row([
                    ft.Text(label, color=color, size=14),
                    ft.Text(val_str, weight=ft.FontWeight.BOLD, color=color, size=14)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

            txt_breakdown.controls = [
                breakdown_row("Block Hours Income", f"{total_bh_income:,.2f}"),
                breakdown_row(f"Per Diem Base", f"{holding_amount:,.2f}"),
                breakdown_row("Per Diem (THB)", f"{per_diem_thb:,.2f}"),
                breakdown_row("Base + Allowance", f"{base_salary + position_allowance:,.2f}"),
                breakdown_row("Transport", f"{transport_income:,.2f}"),
            ]
            page.update()
            
            # Update Persistence State
            for k, ref in refs.items():
                if isinstance(ref, ft.TextField):
                    save_setting(k, ref.value)
                elif isinstance(ref, ft.Dropdown):
                    save_setting(k, ref.value)

        except Exception as ex:
            print(f"Calc Error: {ex}")

    # --- UI Components ---
    def create_input(label, key, icon=None, numeric=True, expand=True, read_only=False):
        val = str(get_setting(key))
        field = ft.TextField(
            label=label,
            value=val,
            keyboard_type=ft.KeyboardType.NUMBER if numeric else ft.KeyboardType.TEXT,
            on_change=calculate,
            expand=expand,
            border_radius=12,
            filled=True,
            prefix_icon=icon,
            content_padding=15,
            text_size=14,
            height=60,
            read_only=read_only
        )
        refs[key] = field
        return field

    # --- Login System ---
    def show_login_dialog(e):
        dlg_username = ft.TextField(label="Username", autofocus=True)
        dlg_pin = ft.TextField(label="PIN (4 digits)", password=True, max_length=4, keyboard_type=ft.KeyboardType.NUMBER)
        
        def close_dlg(e):
            login_dialog.open = False
            page.update()

        def handle_login(e):
            username = dlg_username.value.strip()
            pin = dlg_pin.value.strip()
            
            if not username or not pin:
                page.snack_bar = ft.SnackBar(ft.Text("Please enter both Username and PIN"), bgcolor=ft.Colors.RED)
                page.snack_bar.open = True
                page.update()
                return

            filepath = get_user_file(username)
            if os.path.exists(filepath):
                # Login Existing
                try:
                    with open(filepath, "r") as f:
                        saved_user = json.load(f)
                    if saved_user.get("pin") == pin:
                        # Success
                        current_user.update(saved_user)
                        current_user["is_logged_in"] = True
                        current_user["username"] = username
                        
                        # Refresh UI
                        for k, ref in refs.items():
                            if k in current_user["data"]:
                                ref.value = str(current_user["data"][k])
                        calculate()
                        
                        page.snack_bar = ft.SnackBar(ft.Text(f"Welcome back, {username}!"), bgcolor=ft.Colors.GREEN)
                        login_btn.text = f"User: {username}"
                        login_dialog.open = False
                    else:
                        page.snack_bar = ft.SnackBar(ft.Text("Wrong PIN! Access Denied."), bgcolor=ft.Colors.RED)
                except Exception as ex:
                    page.snack_bar = ft.SnackBar(ft.Text(f"Corrupt Profile: {ex}"), bgcolor=ft.Colors.RED)
            else:
                # Register New
                current_user["username"] = username
                current_user["pin"] = pin
                current_user["is_logged_in"] = True
                current_user["data"] = DEFAULT_VALUES.copy() # Start fresh or keep current? Let's start default.
                
                save_current_profile()
                
                # Refresh UI (reset to defaults for new user)
                for k, ref in refs.items():
                    val = current_user["data"].get(k, DEFAULT_VALUES.get(k))
                    ref.value = str(val)
                calculate()
                
                page.snack_bar = ft.SnackBar(ft.Text(f"Profile Created: {username}"), bgcolor=ft.Colors.GREEN)
                login_btn.text = f"User: {username}"
                login_dialog.open = False
            
            page.snack_bar.open = True
            page.update()

        login_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Login / Register"),
            content=ft.Column([
                ft.Text("Enter a Username to Load/Create profile."),
                dlg_username,
                dlg_pin
            ], height=200, tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=close_dlg),
                ft.ElevatedButton("Login / Create", on_click=handle_login),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.dialog = login_dialog
        login_dialog.open = True
        page.update()

    def handle_logout(e):
        current_user["is_logged_in"] = False
        current_user["username"] = None
        current_user["data"] = DEFAULT_VALUES.copy()
        
        login_btn.text = "Login"
        
        # Reset UI
        for k, ref in refs.items():
            ref.value = str(DEFAULT_VALUES.get(k))
        calculate()
        
        page.snack_bar = ft.SnackBar(ft.Text("Logged Out"), bgcolor=ft.Colors.GREY)
        page.snack_bar.open = True
        page.update()

    login_btn = ft.ElevatedButton("Login", icon=ft.Icons.LOGIN, on_click=show_login_dialog, color=ft.Colors.WHITE, bgcolor=ft.Colors.TEAL_700)
    
    # Toggle Theme
    def toggle_theme(e):
        page.theme_mode = ft.ThemeMode.DARK if page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
        e.control.icon = ft.Icons.DARK_MODE if page.theme_mode == ft.ThemeMode.LIGHT else ft.Icons.LIGHT_MODE
        page.update()

    # AppBar
    page.appbar = ft.AppBar(
        title=ft.Text("Salary App (Pro)"),
        center_title=False,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        actions=[
            login_btn,
            ft.IconButton(ft.Icons.LOGOUT, tooltip="Logout", on_click=handle_logout),
            ft.IconButton(ft.Icons.DARK_MODE, on_click=toggle_theme)
        ]
    )

    # --- Fetch Rates Logic ---
    def fetch_rates(e):
        try:
            e.control.disabled = True
            page.update()
            
            url = "https://open.er-api.com/v6/latest/USD"
            resp = requests.get(url, timeout=5)
            data = resp.json()
            
            if data.get("result") == "success":
                rates = data["rates"]
                usd_thb = rates.get("THB", 0)
                usd_twd = rates.get("TWD", 0)
                
                if usd_thb and usd_twd:
                    refs["superrich_rate_usd"].value = f"{usd_thb:.2f}"
                    refs["cathay_rate"].value = f"{usd_twd:.2f}"
                    twd_thb = usd_thb / usd_twd
                    refs["superrich_rate_twd"].value = f"{twd_thb:.2f}"
                    
                    page.snack_bar = ft.SnackBar(ft.Text("Rates updated!"), bgcolor=ft.Colors.GREEN)
                    calculate()
                else:
                     page.snack_bar = ft.SnackBar(ft.Text("Rate data missing"), bgcolor=ft.Colors.RED)
            else:
                page.snack_bar = ft.SnackBar(ft.Text("API Error"), bgcolor=ft.Colors.RED)
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED)
        finally:
            page.snack_bar.open = True
            e.control.disabled = False
            page.update()


    # --- Layout ---
    # Hero
    hero_card = ft.Container(
        content=ft.Column([
            ft.Text("Total Estimated Income", size=14, color=ft.Colors.WHITE70),
            txt_result_total,
            ft.Divider(color=ft.Colors.WHITE24, thickness=1),
            ft.Container(content=txt_breakdown, padding=ft.Padding(0, 10, 0, 0))
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        gradient=ft.LinearGradient(
            begin=ft.alignment.Alignment(-1, -1),
            end=ft.alignment.Alignment(1, 1),
            colors=[ft.Colors.TEAL_400, ft.Colors.TEAL_800],
        ),
        padding=30,
        border_radius=20,
        shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLUE_GREY_100, offset=ft.Offset(0, 10))
    )

    def section_header(title, icon):
        return ft.Row([
            ft.Icon(icon, color=ft.Colors.PRIMARY),
            ft.Text(title, size=16, weight=ft.FontWeight.BOLD)
        ])

    # Time Inputs
    time_card = ft.Card(
        elevation=2,
        content=ft.Container(
            padding=20,
            content=ft.Column([
                section_header("Time Inputs", ft.Icons.ACCESS_TIME_ROUNDED),
                ft.Container(height=10),
                ft.Row([create_input("BH Hours", "bh_hours", ft.Icons.TIMELAPSE), create_input("BH Mins", "bh_mins")]),
                ft.Row([create_input("EUR.AME.AUS", "p1_hours", ft.Icons.AIRPLANE_TICKET), create_input("Mins", "p1_mins", expand=False)]),
                ft.Row([create_input("Other regions", "p2_hours", ft.Icons.FLIGHT_TAKEOFF), create_input("Mins", "p2_mins", expand=False)]),
            ], spacing=15)
        )
    )

    # Rates Inputs
    rates_card = ft.Card(
        elevation=2,
        content=ft.Container(
            padding=20,
            content=ft.Column([
                ft.Row([
                    section_header("Rates & Config", ft.Icons.CURRENCY_EXCHANGE),
                    ft.IconButton(ft.Icons.CLOUD_SYNC, on_click=fetch_rates, tooltip="Update Live Rates")
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=10),
                ft.Row([create_input("Base Salary", "base_salary"), create_input("Position Allow.", "position_allowance")]),
                ft.Divider(),
                ft.Row([create_input("Normal Rate", "normal_rate"), create_input("Transport Rate", "transport_rate")]),
                ft.Row([create_input("OT Rate (2.5x)", "ot_rate", read_only=True), create_input("Super OT (3.5x)", "super_ot_rate", read_only=True)]),
                ft.Divider(),
                ft.Row([create_input("Per Diem (Euro Mult)", "per_diem_euro_mult"), create_input("Per Diem (Other Mult)", "per_diem_other_mult")]),
            ], spacing=15)
        )
    )
    
    # Currency Settings
    dd_currency = ft.Dropdown(
        label="Withdrawal Currency",
        value=str(get_setting("withdrawal_currency")),
        options=[ft.dropdown.Option("USD"), ft.dropdown.Option("TWD")],
        on_change=calculate,
        border_radius=12,
        filled=True,
        expand=True
    )
    refs["withdrawal_currency"] = dd_currency

    currency_card = ft.Card(
        elevation=2,
        content=ft.Container(
            padding=20,
            content=ft.Column([
                section_header("Exchange Settings", ft.Icons.MONETIZATION_ON),
                ft.Container(height=10),
                ft.Row([dd_currency]),
                ft.Row([create_input("Cathay Rate (USD->TWD)", "cathay_rate"), create_input("Transport Trips", "transport_trips")]),
                ft.Row([create_input("SuperRich (USD->THB)", "superrich_rate_usd"), create_input("SuperRich (TWD->THB)", "superrich_rate_twd")])
            ], spacing=15)
        )
    )

    # Assembly
    page.add(
        ft.Column(
            [
                hero_card,
                time_card,
                rates_card,
                currency_card,
                ft.Text("   ", size=50) # Spacer
            ],
            scroll=ft.ScrollMode.HIDDEN # Main scroll handled by page
        )
    )
    
    # Init Calc
    calculate()

if __name__ == "__main__":
    env_port = os.getenv("PORT")
    if env_port:
        ft.app(target=main, port=int(env_port))
    else:
        ft.app(target=main)
