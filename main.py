import flet as ft
import math
import json
import os
import requests # Added for API

# --- Configuration & Constants ---
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

# --- Main App ---
def main(page: ft.Page):
    # --- Persistence Logic (Client Side) ---
    # Requires FLET_SECRET_KEY to be set in environment variables!
    def get_setting(key):
        try:
            if page.client_storage.contains_key(key):
                val = page.client_storage.get(key)
                return val
        except Exception as e:
            print(f"Storage Error (get {key}): {e}")
        return DEFAULT_VALUES.get(key)

    def save_setting(key, value):
        try:
            page.client_storage.set(key, value)
        except Exception as e:
            print(f"Storage Error (set {key}): {e}")

    # 1. Page Configuration
    page.title = "Salary App (Premium)"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.padding = 0  # handling padding in containers
    page.bgcolor = ft.Colors.GREY_50
    
    # Theme Setup
    page.theme = ft.Theme(
        color_scheme_seed=ft.Colors.TEAL, # Softer look
        visual_density=ft.VisualDensity.COMFORTABLE,
        font_family="Roboto"
    )

    def toggle_theme(e):
        page.theme_mode = ft.ThemeMode.DARK if page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
        e.control.icon = ft.Icons.DARK_MODE if page.theme_mode == ft.ThemeMode.LIGHT else ft.Icons.LIGHT_MODE
        page.update()

    page.appbar = ft.AppBar(
        title=ft.Text("Salary App (Premium)"),
        center_title=True,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        actions=[
            ft.IconButton(ft.Icons.DARK_MODE, on_click=toggle_theme)
        ]
    )

    # --- State & Refs ---
    refs = {}

    # Result Controls
    txt_result_total = ft.Text("0.00 THB", size=40, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
    txt_breakdown = ft.Column(spacing=2)

    # --- Calculation Logic ---
    def calculate(e=None):
        try:
            # Helper to safely float
            def val(key):
                v = refs[key].value
                return float(v) if v else 0.0

            # 1. Get Values
            bh_hours = val("bh_hours")
            bh_mins = val("bh_mins")
            p1_hours = val("p1_hours")
            p1_mins = val("p1_mins")
            p2_hours = val("p2_hours")
            p2_mins = val("p2_mins")

            normal_rate = val("normal_rate")
            # Enforce 2.5x and 3.5x
            ot_rate = normal_rate * 2.5
            super_ot_rate = normal_rate * 3.5
            
            # Update read-only fields for visibility
            if "ot_rate" in refs: refs["ot_rate"].value = f"{ot_rate:.2f}"
            if "super_ot_rate" in refs: refs["super_ot_rate"].value = f"{super_ot_rate:.2f}"
            
            per_diem_euro_mult = val("per_diem_euro_mult")
            per_diem_other_mult = val("per_diem_other_mult")
            
            base_salary = val("base_salary")
            position_allowance = val("position_allowance")
            
            transport_trips = val("transport_trips")
            transport_rate = val("transport_rate")
            
            cathay_rate = val("cathay_rate")
            
            # Select conversion rate
            withdraw_currency = refs["withdrawal_currency"].value
            if withdraw_currency == "USD":
                superrich_rate = val("superrich_rate_usd")
            else:
                superrich_rate = val("superrich_rate_twd")

            # 2. Logic
            # Block Hours
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
            total_per_diem_units = (per_diem_euro_mult * p1_total) + (per_diem_other_mult * p2_total)
            per_diem_base_usd = total_per_diem_units

            # Conversion
            if withdraw_currency == "TWD":
                holding_amount = per_diem_base_usd * cathay_rate
                per_diem_thb = holding_amount * superrich_rate
            else:
                holding_amount = per_diem_base_usd
                per_diem_thb = holding_amount * superrich_rate

            # Other
            transport_income = transport_trips * transport_rate

            # Total
            grand_total_thb = total_bh_income + per_diem_thb + base_salary + position_allowance + transport_income

            # 3. Update UI
            txt_result_total.value = f"{grand_total_thb:,.2f} THB"
            
            # Styles for breakdown
            def breakdown_row(label, val_str, color=ft.Colors.WHITE):
                return ft.Row([
                    ft.Text(label, color=color, size=14),
                    ft.Text(val_str, weight=ft.FontWeight.BOLD, color=color, size=14)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

            txt_breakdown.controls = [
                breakdown_row("Block Hours Income", f"{total_bh_income:,.2f}"),
                breakdown_row(f"Per Diem ({withdraw_currency})", f"{holding_amount:,.2f}"),
                breakdown_row("Per Diem (Converted)", f"{per_diem_thb:,.2f}"),
                breakdown_row("Base + Allowance", f"{base_salary + position_allowance:,.2f}"),
                breakdown_row("Transport", f"{transport_income:,.2f}"),
            ]
            page.update()
            
            # 4. Save
            for k, ref in refs.items():
                if ref.value is not None:
                     save_setting(k, ref.value)

        except Exception as ex:
            print(f"Calc Error: {ex}")

    # --- API Logic ---
    def fetch_rates(e):
        try:
            # disable button to show loading?
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
                    # Update Refs
                    refs["superrich_rate_usd"].value = f"{usd_thb:.2f}"
                    refs["cathay_rate"].value = f"{usd_twd:.2f}"
                    
                    # Calculate TWD -> THB (Cross rate)
                    twd_thb = usd_thb / usd_twd
                    refs["superrich_rate_twd"].value = f"{twd_thb:.2f}"
                    
                    page.snack_bar = ft.SnackBar(ft.Text("Rates updated successfully!"), bgcolor=ft.Colors.GREEN)
                    page.snack_bar.open = True
                    page.update()
                    calculate() # Recalculate totals
                else:
                     page.snack_bar = ft.SnackBar(ft.Text("Could not find THB/TWD in API response."), bgcolor=ft.Colors.RED)
                     page.snack_bar.open = True
                     page.update()
            else:
                page.snack_bar = ft.SnackBar(ft.Text("API Error: " + data.get("result", "Unknown")), bgcolor=ft.Colors.RED)
                page.snack_bar.open = True
                page.update()
                
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Connection Error: {ex}"), bgcolor=ft.Colors.RED)
            page.snack_bar.open = True
            page.update()
        finally:
            e.control.disabled = False
            page.update()

    # --- UI Helpers ---
    def create_input(label, key, icon=None, numeric=True, expand=True, read_only=False):
        val = get_setting(key)
        field = ft.TextField(
            label=label,
            value=str(val),
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

    # --- Layout Construction ---

    # 1. Hero Result Section
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
            colors=[ft.Colors.TEAL_400, ft.Colors.TEAL_800], # Softer Teal Gradient
        ),
        padding=30,
        border_radius=20,
        shadow=ft.BoxShadow(
            blur_radius=20,
            color=ft.Colors.BLUE_GREY_100,
            offset=ft.Offset(0, 10),
            spread_radius=0,
        )
    )

    # 2. Input Groups
    def section_header(title, icon):
        return ft.Row([
            ft.Icon(icon, color=ft.Colors.PRIMARY),
            ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE)
        ], alignment=ft.MainAxisAlignment.START)

    # Time Inputs
    time_card = ft.Card(
        elevation=2,
        # surface_tint_color removed as not supported
        content=ft.Container(
            padding=20,
            content=ft.Column([
                section_header("Time Inputs", ft.Icons.ACCESS_TIME_ROUNDED),
                ft.Container(height=10),
                ft.Row([
                    create_input("BH Hours", "bh_hours", ft.Icons.TIMELAPSE), 
                    create_input("BH Mins", "bh_mins")
                ]),
                ft.Row([
                    create_input("EUR.AME.AUS", "p1_hours", ft.Icons.AIRPLANE_TICKET), 
                    create_input("Mins", "p1_mins", expand=False)
                ]),
                ft.Row([
                    create_input("Other regions", "p2_hours", ft.Icons.FLIGHT_TAKEOFF), 
                    create_input("Mins", "p2_mins", expand=False)
                ]),
            ], spacing=15)
        )
    )

    # Rates & Configuration
    
    # Currency Dropdown logic
    dropdown_curr = ft.Dropdown(
        label="Withdraw Currency",
        options=[ft.dropdown.Option("USD"), ft.dropdown.Option("TWD")],
        value=get_setting("withdrawal_currency"),
        on_select=calculate,
        border_radius=12,
        filled=True,
        height=60,
        expand=True
    )
    refs["withdrawal_currency"] = dropdown_curr

    rates_card = ft.Card(
        elevation=2,
        content=ft.Container(
            padding=20,
            content=ft.Column([
                ft.Row([
                    section_header("Configuration & Rates", ft.Icons.SETTINGS),
                    ft.IconButton(ft.Icons.CLOUD_SYNC, tooltip="Update Live Rates", on_click=fetch_rates, icon_color=ft.Colors.PRIMARY)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Container(height=10),
                
                ft.Text("Hourly Rates (Base -> Auto Calc OT)", size=12, color=ft.Colors.PRIMARY, weight=ft.FontWeight.BOLD),
                ft.Row([create_input("Normal", "normal_rate"), create_input("OT (2.5x)", "ot_rate", read_only=True), create_input("Super OT (3.5x)", "super_ot_rate", read_only=True)]),
                
                ft.Divider(height=20),
                ft.Text("Base & Transport", size=12, color=ft.Colors.PRIMARY, weight=ft.FontWeight.BOLD),
                ft.Row([create_input("Base Salary", "base_salary", ft.Icons.ACCOUNT_BALANCE_WALLET), create_input("Allowance", "position_allowance")]),
                ft.Row([create_input("Trip Rate", "transport_rate", ft.Icons.DIRECTIONS_CAR), create_input("Trips", "transport_trips")]),
                
                ft.Divider(height=20),
                ft.Text("Currency & Exchange", size=12, color=ft.Colors.PRIMARY, weight=ft.FontWeight.BOLD),
                ft.Row([dropdown_curr]),
                ft.Row([create_input("Cathay (USD->TWD)", "cathay_rate"), create_input("SuperRich (USD->THB)", "superrich_rate_usd")]),
                ft.Row([create_input("SuperRich (TWD->THB)", "superrich_rate_twd", expand=True)]),
                
                ft.Divider(height=20),
                ft.Text("Per Diem Multipliers", size=12, color=ft.Colors.PRIMARY, weight=ft.FontWeight.BOLD),
                ft.Row([create_input("Euro Zone", "per_diem_euro_mult", ft.Icons.EURO), create_input("Other Zone", "per_diem_other_mult", ft.Icons.PUBLIC)]),

            ], spacing=10)
        )
    )

    # Main Layout Assembly
    main_layout = ft.Container(
        content=ft.Column([
            hero_card,
            ft.Container(height=10),
            time_card,
            ft.Container(height=5),
            rates_card,
            ft.Container(height=20),
            ft.Text("Salary App v1.1", size=12, color=ft.Colors.GREY_400, italic=True, text_align=ft.TextAlign.CENTER)
        ], scroll=ft.ScrollMode.HIDDEN), # Main column
        
        # Centered constrain
        width=600, 
        padding=20,
        alignment=ft.alignment.Alignment(0, -1)
    )
    
    # Outer container for centering on screen
    page.add(ft.Container(
        content=main_layout,
        alignment=ft.alignment.Alignment(0, -1),
        expand=True
    ))

    # Initial Calc
    calculate()

if __name__ == "__main__":
    # Web Deployment Logic
    # Check if running in a container/server (Environment variable PORT is usually set)
    env_port = os.getenv("PORT")
    if env_port:
        ft.app(target=main, port=int(env_port))
    else:
        ft.app(target=main)
