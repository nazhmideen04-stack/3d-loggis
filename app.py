import os
import re
import sys
import json
import base64
import subprocess
from datetime import datetime
import numpy as np
import streamlit as st
from playwright.sync_api import sync_playwright

# 1. ФИРМЕННАЯ ТЕМА STREAMLIT
os.makedirs(".streamlit", exist_ok=True)
config_path = os.path.join(".streamlit", "config.toml")
target_config = """[theme]
primaryColor = "#00C8E6"
backgroundColor = "#0A0E17"
secondaryBackgroundColor = "#0E182A"
textColor = "#D2DEEC"
font = "sans serif"
"""
if not os.path.exists(config_path) or open(config_path, "r", encoding="utf-8").read() != target_config:
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(target_config)

st.set_page_config(page_title="CATERİNG - THY", layout="wide", initial_sidebar_state="collapsed")

URL = "https://loggis2.com/?company-id=20ce6d9f-398b-43b3-a452-3580dae39122&project-id=2d381d12-d966-4c90-a7c8-c90d6f758ae0&token-id=6e73d15f-0b2f-4d93-a152-3464f7450e50"

LOGO_PATH = "logo.jpg" if os.path.exists("logo.jpg") else "logo.png"
MODEL_PATH = "tunnel_model.glb"

# Полный список ваших дат для исторической команды времени
AVAILABLE_DATES = [
    "08.09.2025 17:00", "08.09.2025 18:00", "08.09.2025 20:00", "08.09.2025 21:00", "08.09.2025 22:00", "08.09.2025 23:00",
    "09.09.2025 00:00", "09.09.2025 01:00", "09.09.2025 02:00", "09.09.2025 03:00", "09.09.2025 04:00", "09.09.2025 05:00",
    "09.09.2025 14:00", "09.09.2025 15:00", "09.09.2025 16:00", "09.09.2025 17:00", "09.09.2025 18:00", "09.09.2025 19:00",
    "09.09.2025 20:00", "09.09.2025 21:00", "09.09.2025 22:00", "09.09.2025 23:00", "10.09.2025 00:00", "10.09.2025 01:00",
    "10.09.2025 02:00", "10.09.2025 03:00", "10.09.2025 04:00", "10.09.2025 05:00", "10.09.2025 06:00", "10.09.2025 07:00",
    "10.09.2025 08:00", "10.09.2025 09:00", "10.09.2025 10:00", "10.09.2025 11:00", "10.09.2025 12:00", "10.09.2025 13:00",
    "10.09.2025 14:00", "10.09.2025 15:00", "10.09.2025 16:00", "10.09.2025 17:00", "10.09.2025 18:00", "10.09.2025 19:00",
    "10.09.2025 20:00", "10.09.2025 21:00", "10.09.2025 22:00", "10.09.2025 23:00", "11.09.2025 00:00", "11.09.2025 01:00",
    "11.09.2025 02:00", "11.09.2025 03:00", "11.09.2025 04:00", "11.09.2025 05:00", "11.09.2025 06:00", "11.09.2025 07:00",
    "11.09.2025 08:00", "11.09.2025 09:00", "11.09.2025 10:00", "11.09.2025 11:00", "11.09.2025 12:00", "11.09.2025 13:00",
    "11.09.2025 14:00", "11.09.2025 15:00", "11.09.2025 16:00", "11.09.2025 17:00", "11.09.2025 18:00", "11.09.2025 19:00",
    "11.09.2025 20:00", "11.09.2025 21:00", "11.09.2025 22:00", "11.09.2025 23:00", "12.09.2025 00:00", "12.09.2025 01:00",
    "12.09.2025 02:00", "12.09.2025 03:00", "12.09.2025 11:00", "12.09.2025 12:00", "12.09.2025 13:00", "12.09.2025 14:00",
    "12.09.2025 15:00", "12.09.2025 16:00", "13.09.2025 06:00", "13.09.2025 07:00", "13.09.2025 08:00", "13.09.2025 09:00",
    "13.09.2025 10:00", "13.09.2025 11:00", "13.09.2025 12:00", "13.09.2025 13:00", "13.09.2025 14:00", "13.09.2025 15:00",
    "14.09.2025 05:00", "14.09.2025 06:00", "14.09.2025 07:00", "14.09.2025 08:00", "14.09.2025 09:00", "14.09.2025 10:00",
    "14.09.2025 11:00", "14.09.2025 12:00", "14.09.2025 13:00", "14.09.2025 14:00", "14.09.2025 15:00", "14.09.2025 16:00",
    "14.09.2025 17:00", "14.09.2025 18:00", "14.09.2025 19:00", "14.09.2025 20:00", "14.09.2025 21:00", "14.09.2025 22:00",
    "14.09.2025 23:00", "15.09.2025 00:00", "15.09.2025 01:00", "15.09.2025 02:00", "15.09.2025 03:00", "15.09.2025 04:00",
    "15.09.2025 05:00", "15.09.2025 06:00", "15.09.2025 07:00", "15.09.2025 08:00", "15.09.2025 09:00", "15.09.2025 10:00",
    "15.09.2025 11:00", "15.09.2025 12:00", "15.09.2025 13:00", "15.09.2025 14:00", "15.09.2025 15:00", "15.09.2025 16:00",
    "15.09.2025 17:00", "15.09.2025 18:00", "15.09.2025 19:00", "15.09.2025 20:00", "15.09.2025 21:00", "15.09.2025 22:00",
    "15.09.2025 23:00", "16.09.2025 00:00", "16.09.2025 01:00", "16.09.2025 02:00", "16.09.2025 03:00", "16.09.2025 04:00",
    "16.09.2025 05:00", "16.09.2025 06:00", "16.09.2025 07:00", "16.09.2025 08:00", "16.09.2025 09:00", "16.09.2025 10:00",
    "16.09.2025 11:00", "16.09.2025 12:00", "16.09.2025 13:00", "16.09.2025 14:00", "16.09.2025 15:00", "16.09.2025 16:00",
    "16.09.2025 17:00", "16.09.2025 18:00", "16.09.2025 19:00", "16.09.2025 20:00", "16.09.2025 21:00", "16.09.2025 22:00",
    "16.09.2025 23:00", "17.09.2025 00:00", "17.09.2025 01:00", "17.09.2025 02:00", "17.09.2025 03:00", "17.09.2025 04:00",
    "17.09.2025 05:00", "17.09.2025 06:00", "17.09.2025 07:00", "17.09.2025 08:00", "17.09.2025 09:00", "17.09.2025 10:00",
    "17.09.2025 13:00", "17.09.2025 14:00", "17.09.2025 15:00", "17.09.2025 16:00", "17.09.2025 17:00", "17.09.2025 18:00",
    "17.09.2025 19:00", "17.09.2025 20:00", "17.09.2025 21:00", "17.09.2025 22:00", "17.09.2025 23:00", "18.09.2025 00:00",
    "18.09.2025 01:00", "18.09.2025 02:00", "18.09.2025 03:00", "18.09.2025 04:00", "18.09.2025 05:00", "18.09.2025 06:00",
    "18.09.2025 07:00", "18.09.2025 08:00", "18.09.2025 09:00", "18.09.2025 10:00", "18.09.2025 11:00", "18.09.2025 12:00",
    "18.09.2025 13:00", "18.09.2025 14:00", "18.09.2025 15:00", "18.09.2025 16:00", "18.09.2025 17:00", "18.09.2025 18:00",
    "18.09.2025 19:00", "18.09.2025 20:00", "18.09.2025 21:00", "18.09.2025 22:00", "18.09.2025 23:00", "19.09.2025 00:00",
    "19.09.2025 01:00", "19.09.2025 02:00", "19.09.2025 03:00", "19.09.2025 04:00", "19.09.2025 05:00", "19.09.2025 06:00",
    "19.09.2025 07:00", "19.09.2025 08:00", "19.09.2025 09:00", "19.09.2025 10:00", "19.09.2025 11:00", "19.09.2025 12:00",
    "19.09.2025 13:00", "19.09.2025 14:00", "19.09.2025 15:00", "19.09.2025 16:00", "19.09.2025 17:00", "19.09.2025 18:00",
    "19.09.2025 19:00", "19.09.2025 20:00", "19.09.2025 21:00", "19.09.2025 22:00", "19.09.2025 23:00", "20.09.2025 00:00",
    "20.09.2025 01:00", "20.09.2025 02:00", "20.09.2025 03:00", "20.09.2025 04:00", "20.09.2025 05:00", "20.09.2025 06:00",
    "20.09.2025 07:00", "20.09.2025 08:00", "20.09.2025 09:00", "20.09.2025 10:00", "20.09.2025 11:00", "20.09.2025 12:00",
    "20.09.2025 13:00", "20.09.2025 14:00", "20.09.2025 15:00", "20.09.2025 16:00", "20.09.2025 17:00", "20.09.2025 18:00",
    "20.09.2025 19:00", "20.09.2025 20:00", "20.09.2025 21:00", "20.09.2025 22:00", "20.09.2025 23:00", "21.09.2025 00:00",
    "21.09.2025 01:00", "21.09.2025 02:00", "21.09.2025 03:00", "21.09.2025 04:00", "21.09.2025 05:00", "21.09.2025 06:00",
    "21.09.2025 07:00", "21.09.2025 08:00", "21.09.2025 09:00", "21.09.2025 10:00", "21.09.2025 11:00", "21.09.2025 12:00",
    "21.09.2025 13:00", "21.09.2025 14:00", "21.09.2025 15:00", "21.09.2025 16:00", "21.09.2025 17:00", "21.09.2025 18:00",
    "21.09.2025 19:00", "21.09.2025 20:00", "21.09.2025 21:00", "21.09.2025 22:00", "21.09.2025 23:00", "22.09.2025 00:00",
    "22.09.2025 01:00", "22.09.2025 02:00", "22.09.2025 03:00", "22.09.2025 04:00", "22.09.2025 05:00", "22.09.2025 06:00",
    "22.09.2025 07:00", "22.09.2025 08:00", "22.09.2025 09:00", "22.09.2025 10:00", "22.09.2025 11:00", "22.09.2025 12:00",
    "22.09.2025 13:00", "22.09.2025 14:00", "22.09.2025 15:00", "22.09.2025 16:00", "22.09.2025 17:00", "22.09.2025 18:00",
    "22.09.2025 19:00", "22.09.2025 20:00", "22.09.2025 21:00", "22.09.2025 22:00", "22.09.2025 23:00", "23.09.2025 00:00",
    "23.09.2025 01:00", "23.09.2025 02:00", "23.09.2025 03:00", "23.09.2025 04:00", "23.09.2025 05:00", "23.09.2025 06:00",
    "23.09.2025 07:00", "23.09.2025 08:00", "23.09.2025 09:00", "23.09.2025 10:00", "23.09.2025 11:00", "23.09.2025 12:00",
    "23.09.2025 13:00", "23.09.2025 14:00", "23.09.2025 15:00", "23.09.2025 16:00", "23.09.2025 17:00", "23.09.2025 18:00",
    "23.09.2025 19:00", "23.09.2025 20:00", "23.09.2025 21:00", "23.09.2025 22:00", "23.09.2025 23:00", "24.09.2025 00:00",
    "24.09.2025 01:00", "24.09.2025 02:00", "24.09.2025 03:00", "24.09.2025 04:00", "24.09.2025 05:00", "24.09.2025 06:00",
    "24.09.2025 07:00", "24.09.2025 08:00", "24.09.2025 09:00", "24.09.2025 10:00", "24.09.2025 11:00", "24.09.2025 12:00",
    "24.09.2025 13:00", "24.09.2025 14:00", "24.09.2025 15:00", "24.09.2025 16:00", "24.09.2025 17:00", "24.09.2025 18:00",
    "24.09.2025 19:00", "24.09.2025 20:00", "24.09.2025 21:00", "24.09.2025 22:00", "24.09.2025 23:00"
]

# Фирменный стиль DESTECH с мобильной адаптацией
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;600;700&family=Syne:wght@700;800&display=swap');

    :root {
        --primary-color: #00C8E6 !important;
        accent-color: #00C8E6 !important;
    }

    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #0A0E17 !important;
    }

    html, body, [class*="css"], p, span, label, .stMarkdown {
        font-family: 'Chakra Petch', sans-serif !important;
        color: #D2DEEC;
    }

    h1, h2, h3 {
        font-family: 'Syne', sans-serif !important;
        font-weight: 800 !important;
        letter-spacing: 1.5px !important;
        text-transform: uppercase;
        color: #FFFFFF !important;
        text-shadow: none !important;
    }

    code {
        background-color: transparent !important;
        color: #00C8E6 !important;
        border: none !important;
        padding: 0 !important;
        font-weight: 700 !important;
    }

    [data-testid="stMetricValue"], .neon-data {
        color: #00C8E6 !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #8397AD !important;
        font-size: 13px !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Радиокнопки */
    div[data-testid="stRadio"] > label {
        font-family: 'Chakra Petch', sans-serif !important;
        font-size: 14px !important;
        color: #8397AD !important;
        font-weight: 600 !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] label p {
        font-family: 'Chakra Petch', sans-serif !important;
        font-size: 18px !important;
        color: #E6F0FA !important;
        font-weight: 600 !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) div:first-child {
        transform: scale(1.2) !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) div:first-child div {
        background-color: #00C8E6 !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] > label {
        margin-bottom: 12px !important;
        cursor: pointer !important;
        display: flex !important;
        align-items: center !important;
    }

    div[data-baseweb="select"] {
        background-color: #0E182A !important;
        border: 1px solid rgba(0, 200, 230, 0.4) !important;
        border-radius: 6px !important;
    }

    /* Слайдер и чекбоксы */
    div[data-testid="stSlider"] div[role="slider"] {
        background-color: #00C8E6 !important;
        border-color: #00C8E6 !important;
        box-shadow: 0 0 14px #00C8E6 !important;
    }

    div[data-testid="stCheckbox"] label:has(input:checked) span[data-baseweb="checkbox"] {
        background-color: #00C8E6 !important;
        border-color: #00C8E6 !important;
    }

    div[data-testid="stCheckbox"] label span[data-baseweb="checkbox"] {
        border-color: #00C8E6 !important;
    }

    div[data-testid="stCheckbox"] svg path {
        fill: #0A0E17 !important;
        stroke: #0A0E17 !important;
    }

    .destech-badge {
        font-family: 'Syne', sans-serif;
        font-size: 15px;
        font-weight: 800;
        letter-spacing: 2px;
        background: #00C8E6;
        color: #000000;
        padding: 5px 14px;
        border-radius: 6px;
        display: inline-block;
    }

    div.stButton > button {
        background-color: #0E2238 !important;
        color: #00C8E6 !important;
        font-family: 'Chakra Petch', sans-serif !important;
        font-size: 15px !important;
        font-weight: 700 !important;
        border: 1px solid rgba(0, 200, 230, 0.4) !important;
        border-radius: 6px !important;
        padding: 9px 20px !important;
        width: 100% !important;
        transition: background-color 0.2s ease, border-color 0.2s ease !important;
    }

    div.stButton > button:hover {
        background-color: #132E4C !important;
        border-color: #00C8E6 !important;
        color: #FFFFFF !important;
    }

    /* МОБИЛЬНАЯ АДАПТАЦИЯ */
    @media (max-width: 820px) {
        .main .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-top: 1.5rem !important;
        }

        [data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: column-reverse !important;
            gap: 1.2rem !important;
        }

        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }

        .header-box h1 {
            font-size: 22px !important;
        }

        .header-box img {
            width: 130px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

LOGO_B64 = ""
if os.path.exists(LOGO_PATH):
    with open(LOGO_PATH, "rb") as f:
        LOGO_B64 = base64.b64encode(f.read()).decode()

LOGO_TAG = f'<img src="data:image/jpeg;base64,{LOGO_B64}" style="width: 180px; height: auto; display: block; opacity: 0.85; border-radius: 4px;" alt="DESTECH">' if LOGO_B64 else '<span class="destech-badge">DESTECH</span>'

st.markdown(f"""
<div class="header-box" style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-top: -20px; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid rgba(0, 200, 230, 0.15);">
    <div style="display: flex; flex-direction: column; justify-content: center;">
        <h1 style="margin: 0 !important; padding: 0 !important; font-size: 30px !important; line-height: 1.1 !important;">CATERİNG - THY</h1>
        <div style="color: #00C8E6; font-weight: 700; font-size: 13px; letter-spacing: 1.5px; margin-top: 3px;">SENSÖR TAKİP SİSTEMİ</div>
    </div>
    <div style="display: flex; align-items: center;">
        {LOGO_TAG}
    </div>
</div>
""", unsafe_allow_html=True)

CATEGORIES = {
    "hoop": {"name": "Othoradial Strains", "tag": "-CS", "title": "Çevresel gerinim (CS)", "unit": "µm/m"},
    "axial": {"name": "Longitudinal Strains", "tag": "-S", "title": "Boyuna gerinim (S)", "unit": "µm/m"},
    "temp": {"name": "Temperature", "tag": "-TP", "title": "Sıcaklık (TP)", "unit": "°C"},
}

def clean_num(s):
    if not s:
        return np.nan
    s = str(s).replace(",", ".").replace(" ", "").strip()
    m = re.search(r"[-+]?\d+(?:\.\d+)?", s)
    return float(m.group()) if m else np.nan

def ensure_playwright_installed():
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    except Exception:
        pass

@st.cache_data(ttl=300)
def fetch_loggis_data(target_date_str=None):
    all_results = {k: {"values": {}, "date": ""} for k in CATEGORIES}

    with sync_playwright() as p:
        browser_args = [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--window-size=1920,1080",
        ]
        try:
            browser = p.chromium.launch(headless=True, args=browser_args)
        except Exception:
            ensure_playwright_installed()
            browser = p.chromium.launch(headless=True, args=browser_args)

        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            timezone_id="Europe/Istanbul",
            locale="fr-FR",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media"] else route.continue_())

        try:
            page.goto(URL, timeout=60000, wait_until="domcontentloaded")
            page.wait_for_timeout(3500)

            try:
                page.get_by_text("Types").click(timeout=8000)
            except Exception:
                pass
            page.wait_for_timeout(1000)

            try:
                page.get_by_role("combobox").first.select_option("MONTH_02", timeout=5000)
            except Exception:
                pass
            page.wait_for_timeout(800)

            # Выбор исторической даты из списка
            if target_date_str and target_date_str != "En Son (Güncel)":
                try:
                    page.get_by_role("combobox").nth(1).select_option(label=target_date_str, timeout=5000)
                except Exception:
                    try:
                        page.get_by_role("combobox").nth(1).select_option(target_date_str, timeout=3000)
                    except Exception:
                        pass
            else:
                try:
                    page.get_by_role("combobox").nth(1).select_option("TABLE_ROW_DATE", timeout=5000)
                except Exception:
                    pass
            page.wait_for_timeout(1000)

            for cat_key, cat_cfg in CATEGORIES.items():
                try:
                    page.get_by_role("listbox").select_option(cat_cfg["name"], timeout=6000)
                except Exception:
                    try:
                        page.locator(f"option:has-text('{cat_cfg['name']}')").first.click(force=True, timeout=4000)
                    except Exception:
                        try:
                            page.get_by_text(cat_cfg["name"]).first.click(force=True, timeout=4000)
                        except Exception:
                            pass

                page.wait_for_timeout(3000)

                val_map = {}
                latest_date_str = ""

                for _ in range(15):
                    try:
                        extracted = page.evaluate("""() => {
                            try {
                                const table = document.querySelector('table');
                                if (!table) return null;

                                const trs = Array.from(table.querySelectorAll('tr'));
                                let headerCells = [];
                                for (const tr of trs) {
                                    const cells = Array.from(tr.querySelectorAll('th, td')).map(c => (c.innerText || '').trim());
                                    if (cells.some(c => c.includes('TA-') || c.includes('TB-'))) {
                                        headerCells = cells;
                                        break;
                                    }
                                }
                                if (headerCells.length === 0 && trs.length > 0) {
                                    headerCells = Array.from(trs[0].querySelectorAll('th, td')).map(c => (c.innerText || '').trim());
                                }

                                const tbody = table.querySelector('tbody') || table;
                                const rows = Array.from(tbody.querySelectorAll('tr'));
                                let dataCells = [];
                                for (const r of rows) {
                                    const cells = Array.from(r.querySelectorAll('td')).map(c => (c.innerText || '').trim());
                                    if (cells.length > 1 && (cells[0].includes('/') || cells[0].includes(':') || cells[0].includes('-'))) {
                                        dataCells = cells;
                                        break;
                                    }
                                }

                                if (headerCells.length === 0 || dataCells.length === 0) return null;
                                return { headers: headerCells, values: dataCells };
                            } catch(e) {
                                return null;
                            }
                        }""")

                        if extracted and extracted.get("values") and extracted.get("headers"):
                            headers = extracted["headers"]
                            values = extracted["values"]
                            latest_date_str = values[0]

                            for h, v_str in zip(headers[1:], values[1:]):
                                if "TA-" in h or "TB-" in h or cat_cfg["tag"] in h:
                                    m = re.search(r"(T[AB]-[A-Za-z0-9\-]+)", h)
                                    s_name = m.group(1) if m else h.split()[0].strip()
                                    v = clean_num(v_str)
                                    if not np.isnan(v):
                                        val_map[s_name] = v

                            if len(val_map) > 0:
                                break
                    except Exception:
                        pass

                    page.wait_for_timeout(600)

                all_results[cat_key] = {"values": val_map, "date": latest_date_str}

        except Exception as e:
            st.warning(f"LoggIS verisi alınırken gecikme oluştu: {e}")
        finally:
            browser.close()

    return all_results

@st.cache_data
def get_model_b64(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

col_nav, col_3d = st.columns([1, 4])

with col_nav:
    st.subheader("KONTROL PANELİ")
    selected_comp = st.radio(
        "Görüntülenecek Bileşen:",
        options=["hoop", "axial", "temp"],
        format_func=lambda k: CATEGORIES[k]["title"]
    )

    st.markdown("---")
    st.subheader("⏱️ Geçmiş Zaman Seçimi")
    
    date_options = ["En Son (Güncel)"] + AVAILABLE_DATES
    selected_date_choice = st.selectbox("Tarih ve Saat Seç:", options=date_options)

    if st.button("Verileri Yenile"):
        st.cache_data.clear()
        st.rerun()

# Загружаем данные с учетом выбранной даты
with st.spinner("LoggIS verileri işleniyor..."):
    current_data = fetch_loggis_data(None if selected_date_choice == "En Son (Güncel)" else selected_date_choice)

cat_cfg = CATEGORIES[selected_comp]
cur_layer = current_data.get(selected_comp, {"values": {}, "date": ""})
raw_v_map = cur_layer["values"]

active_category_values = {}
for s_name, val in raw_v_map.items():
    if val is None or np.isnan(val):
        continue
    u_name = s_name.upper()
    if selected_comp == "hoop" and "-CS" in u_name:
        active_category_values[s_name] = float(val)
    elif selected_comp == "axial":
        if ("-S" in u_name) and ("-CS" not in u_name):
            active_category_values[s_name] = float(val)
    elif selected_comp == "temp" and "-TP" in u_name:
        active_category_values[s_name] = float(val)

vals = [float(v) for v in active_category_values.values() if not np.isnan(v)]
if not vals:
    clim = [-1.0, 1.0]
else:
    real_min = float(min(vals))
    real_max = float(max(vals))
    diff = abs(real_max - real_min)
    if diff < 0.001:
        clim = [round(real_min - 0.5, 2), round(real_max + 0.5, 2)]
    else:
        buf = diff * 0.02
        clim = [round(real_min - buf, 2), round(real_max + buf, 2)]

with col_nav:
    st.markdown("---")
    st.subheader("GÖRÜNÜМ AYARLARI")

    tunnel_opacity = st.slider("Tünel Opaklığı (%):", min_value=0, max_value=100, value=85, step=5) / 100.0
    show_meters = st.checkbox("Metre Cetveli Göster", value=True)
    show_no_data_red = st.checkbox("⚠️ Verisi Olmayan Sensörleri Göster", value=False)

    st.markdown("---")
    st.write("**Aktif Periyot:**")
    st.markdown(f"<span class='neon-data' style='font-size: 13px;'>{selected_date_choice}</span>", unsafe_allow_html=True)
    
    st.write("**Aktif Sensör Sayısı:**")
    st.markdown(f"<span class='neon-data' style='font-size: 18px;'>{len(active_category_values)}</span>", unsafe_allow_html=True)
    
    st.write("**Skala Limitleri (Gerçek Min / Maks):**")
    st.markdown(f"<span class='neon-data' style='font-size: 14px;'>Min: {clim[0]:+.2f} | Maks: {clim[1]:+.2f} {cat_cfg['unit']}</span>", unsafe_allow_html=True)

# --- 3B THREE.JS ОБЛАСТЬ ---
with col_3d:
    sensor_options = ["Seçiniz..."] + sorted(list(active_category_values.keys()))
    
    sel_col1, sel_col2 = st.columns([3, 1])
    with sel_col1:
        selected_sensor = st.selectbox(
            "Sensör Değerini İncele:", 
            options=sensor_options,
            help="Modelde vurgulanacak ve kameranın odaklanacağı sensörü seçin"
        )
    with sel_col2:
        if selected_sensor != "Seçiniz..." and selected_sensor in active_category_values:
            st.metric(
                label=f"Seçilen Sensör Değeri",
                value=f"{active_category_values[selected_sensor]:+.2f} {cat_cfg['unit']}"
            )
        else:
            st.metric(label="Sensör Değeri", value="--")

    model_b64 = get_model_b64(MODEL_PATH)
    
    if not model_b64:
        st.error(f"⚠️ `{MODEL_PATH}` bulunamadı! Lütfen 3ds Max'ten aldığınız .glb modelini `app.py` ile aynı klasöre yükleyiniz.")
    else:
        payload_data = {
            "activeCategoryValues": active_category_values,
            "selectedSensor": selected_sensor,
            "unit": cat_cfg["unit"],
            "clim": clim,
            "comp": selected_comp,
            "tunnelOpacity": float(tunnel_opacity),
            "showMeters": show_meters,
            "showNoDataRed": show_no_data_red
        }
        json_payload = json.dumps(payload_data)

        raw_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        * {
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }
        body {
            margin: 0;
            padding: 0;
            overflow: hidden;
            background-color: #0A0E17;
            font-family: 'Chakra Petch', sans-serif;
            touch-action: none;
        }
        #canvas-container {
            width: 100vw;
            height: 100vh;
            position: relative;
        }
        #sensor-tooltip {
            position: absolute;
            display: none;
            background: rgba(14, 24, 42, 0.95);
            border: 1px solid #00C8E6;
            color: #FFFFFF;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 13px;
            pointer-events: none;
            z-index: 100;
            box-shadow: 0 4px 16px rgba(0, 200, 230, 0.35);
        }
        #selected-hud {
            position: absolute;
            top: 14px;
            left: 14px;
            display: none;
            background: rgba(10, 14, 23, 0.92);
            border: 1px solid #00C8E6;
            padding: 8px 14px;
            border-radius: 8px;
            z-index: 95;
            box-shadow: 0 4px 16px rgba(0, 200, 230, 0.3);
            max-width: 220px;
        }
        #selected-hud .hud-title {
            font-size: 11px;
            color: #8397AD;
            text-transform: uppercase;
            letter-spacing: 0.8px;
        }
        #selected-hud .hud-name {
            font-size: 15px;
            color: #FFFFFF;
            font-weight: 700;
            margin: 1px 0 3px 0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        #selected-hud .hud-val {
            font-size: 18px;
            color: #00E5FF;
            font-weight: 700;
        }
        #loader {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: #00C8E6;
            font-size: 16px;
            font-weight: 700;
            letter-spacing: 1px;
            text-align: center;
            width: 80%;
        }
        #color-legend {
            position: absolute;
            top: 14px;
            right: 14px;
            display: flex;
            flex-direction: column;
            align-items: center;
            background: rgba(10, 14, 23, 0.92);
            padding: 10px 12px;
            border: 1px solid rgba(0, 200, 230, 0.55);
            box-shadow: 0 0 16px rgba(0, 200, 230, 0.25);
            border-radius: 6px;
            z-index: 90;
            user-select: none;
        }
        #legend-title {
            color: #00E5FF;
            font-size: 12px;
            font-weight: 700;
            margin-bottom: 6px;
            text-transform: none !important;
            letter-spacing: 0.5px;
        }
        .legend-bar-container {
            display: flex;
            align-items: stretch;
            height: 180px;
        }
        #legend-bar {
            width: 16px;
            border-radius: 4px;
            border: 1px solid rgba(255, 255, 255, 0.35);
            margin-right: 8px;
        }
        .legend-labels {
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            color: #FFFFFF;
            font-size: 11px;
            font-weight: 700;
        }

        @media (max-width: 600px) {
            #color-legend {
                padding: 6px 8px;
                top: 10px;
                right: 10px;
            }
            .legend-bar-container {
                height: 130px;
            }
            #legend-bar {
                width: 12px;
            }
            #legend-title {
                font-size: 10px;
            }
            .legend-labels {
                font-size: 9px;
            }
            #selected-hud {
                top: 10px;
                left: 10px;
                padding: 6px 10px;
            }
            #selected-hud .hud-name {
                font-size: 13px;
            }
            #selected-hud .hud-val {
                font-size: 15px;
            }
        }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/tween.js/18.6.4/tween.umd.js"></script>
</head>
<body>
    <div id="canvas-container">
        <div id="loader">3B MODEL VE TÜNEL İNTERPOLASYONU YÜKLENİYOR...</div>
        <div id="sensor-tooltip"></div>
        
        <div id="selected-hud">
            <div class="hud-title">Seçilen Sensör</div>
            <div id="hud-sensor-name" class="hud-name">--</div>
            <div id="hud-sensor-val" class="hud-val">--</div>
        </div>

        <div id="color-legend">
            <div id="legend-title"></div>
            <div class="legend-bar-container">
                <div id="legend-bar"></div>
                <div class="legend-labels">
                    <span id="lbl-max">--</span>
                    <span id="lbl-mid">--</span>
                    <span id="lbl-min">--</span>
                </div>
            </div>
        </div>
    </div>

    <script>
        const payload = __INJECT_PAYLOAD__;
        const modelB64 = "__INJECT_MODEL__";
        
        const container = document.getElementById('canvas-container');
        const tooltip = document.getElementById('sensor-tooltip');
        const loaderText = document.getElementById('loader');
        const legendBar = document.getElementById('legend-bar');
        const legendTitle = document.getElementById('legend-title');
        const lblMax = document.getElementById('lbl-max');
        const lblMid = document.getElementById('lbl-mid');
        const lblMin = document.getElementById('lbl-min');

        const selectedHud = document.getElementById('selected-hud');
        const hudName = document.getElementById('hud-sensor-name');
        const hudVal = document.getElementById('hud-sensor-val');

        // =========================================================================
        // СТАБИЛЬНЫЕ СПЕКТРЫ ДЛЯ КАЖДОГО ТИПА (СВЕРХУ ВНИЗ В ЛЕГЕНДЕ: MAX -> MIN)
        // =========================================================================
        const hoopStops = [
            new THREE.Color("#050833"), new THREE.Color("#0044FF"), new THREE.Color("#00D5FF"),
            new THREE.Color("#00FF66"), new THREE.Color("#FFEE00"), new THREE.Color("#FF7700"), new THREE.Color("#FF0022")
        ];
        const axialStops = [
            new THREE.Color("#080038"), new THREE.Color("#2A0A5E"), new THREE.Color("#630F78"),
            new THREE.Color("#9E1B7F"), new THREE.Color("#D32B6E"), new THREE.Color("#F55447"), new THREE.Color("#FF9500")
        ];
        const temperatureStops = [
            new THREE.Color("#020024"), new THREE.Color("#0033FF"), new THREE.Color("#00D8FF"),
            new THREE.Color("#00FF44"), new THREE.Color("#B4FF00"), new THREE.Color("#FFDD00"),
            new THREE.Color("#FF4400"), new THREE.Color("#D50000")
        ];

        let currentStops = hoopStops;
        if (payload.comp === "axial") { currentStops = axialStops; legendTitle.innerText = "Boyuna [µm/m]"; }
        else if (payload.comp === "temp") { currentStops = temperatureStops; legendTitle.innerText = "Sıcaklık [°C]"; }
        else { currentStops = hoopStops; legendTitle.innerText = "Çevresel [µm/m]"; }

        function buildExactLegendGradient(stops) {
            const n = stops.length; const items = [];
            for (let i = 0; i < n; i++) {
                const colorObj = stops[n - 1 - i];
                items.push('#' + colorObj.getHexString() + ' ' + ((i / (n - 1)) * 100).toFixed(1) + '%');
            }
            return 'linear-gradient(to bottom, ' + items.join(', ') + ')';
        }
        legendBar.style.background = buildExactLegendGradient(currentStops);

        function sampleColorRamp(stops, t) {
            t = Math.max(0.0, Math.min(1.0, t));
            const scaled = t * (stops.length - 1);
            const idx = Math.floor(scaled);
            const fract = scaled - idx;
            if (idx >= stops.length - 1) return stops[stops.length - 1].clone();
            const c = new THREE.Color();
            c.lerpColors(stops[idx], stops[idx + 1], fract);
            return c;
        }

        function getColorForValue(val, clim) {
            if (val === undefined || isNaN(val)) return new THREE.Color(0x08111e);
            return sampleColorRamp(currentStops, (val - clim[0]) / ((clim[1] - clim[0]) || 1.0));
        }

        const finalMin = payload.clim[0], finalMax = payload.clim[1];
        lblMax.innerText = (finalMax > 0 ? "+" : "") + finalMax.toFixed(2);
        lblMid.innerText = (((finalMin + finalMax) / 2.0) > 0 ? "+" : "") + ((finalMin + finalMax) / 2.0).toFixed(2);
        lblMin.innerText = (finalMin > 0 ? "+" : "") + finalMin.toFixed(2);

        const scene = new THREE.Scene(); scene.background = new THREE.Color(0x0A0E17);
        const sensorScene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 5000);
        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.autoClear = false; container.appendChild(renderer.domElement);

        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true; controls.dampingFactor = 0.05;

        scene.add(new THREE.AmbientLight(0xffffff, 1.4));
        const dl1 = new THREE.DirectionalLight(0x00E5FF, 1.6); dl1.position.set(60, 100, 80); scene.add(dl1);

        const interactiveSensors = []; const tunnelMeshes = [];
        const raycaster = new THREE.Raycaster(); const mouse = new THREE.Vector2();

        function extractSensorId(name) { const m = name.match(/T[AB]-[A-Za-z0-9\-]+/i); return m ? m[0] : name; }
        function normalizeKey(str) { return String(str).toUpperCase().replace(/[^A-Z0-9]/g, ''); }
        function getCanonicalSensorId(name) {
            const m = name.match(/(T[AB])-([A-Za-z]+)0*(\d+)-([A-Za-z0-9]+)/i);
            return m ? (m[1] + '-' + m[2] + parseInt(m[3], 10) + '-' + m[4]).toUpperCase() : name.toUpperCase();
        }

        const normalizedDataMap = {};
        for (const rawKey in payload.activeCategoryValues) {
            const val = payload.activeCategoryValues[rawKey];
            normalizedDataMap[rawKey.toUpperCase()] = { canonicalKey: rawKey, val: val };
            normalizedDataMap[normalizeKey(rawKey)] = { canonicalKey: rawKey, val: val };
            normalizedDataMap[getCanonicalSensorId(rawKey)] = { canonicalKey: rawKey, val: val };
        }

        function checkSensorData(sensorId) {
            const uId = sensorId.toUpperCase(), nId = normalizeKey(sensorId), cId = getCanonicalSensorId(sensorId);
            if (normalizedDataMap[uId]) return { found: true, key: normalizedDataMap[uId].canonicalKey, val: normalizedDataMap[uId].val };
            if (normalizedDataMap[cId]) return { found: true, key: normalizedDataMap[cId].canonicalKey, val: normalizedDataMap[cId].val };
            if (normalizedDataMap[nId]) return { found: true, key: normalizedDataMap[nId].canonicalKey, val: normalizedDataMap[nId].val };
            return { found: false, key: sensorId, val: NaN };
        }

        const binaryStr = atob(modelB64); const bytes = new Uint8Array(binaryStr.length);
        for (let i = 0; i < binaryStr.length; i++) bytes[i] = binaryStr.charCodeAt(i);

        let selectedMeshRef = null;
        const gltfLoader = new THREE.GLTFLoader();
        gltfLoader.parse(bytes.buffer, '', function(gltf) {
            const model = gltf.scene; scene.add(model); loaderText.style.display = 'none';
            const rawSensors = []; const boxTA = new THREE.Box3(); const boxTB = new THREE.Box3();
            let hasTA = false, hasTB = false;

            model.traverse(function(child) {
                if (child.isMesh) {
                    const uName = child.name.toUpperCase();
                    if (uName.startsWith("TA-") || uName.startsWith("TB-") || uName.includes("-CS") || uName.includes("-S") || uName.includes("-TP")) {
                        rawSensors.push(child);
                    } else if (uName.includes("TUNNEL") || uName.includes("TÜNEL") || uName === "TA" || uName === "TB") {
                        tunnelMeshes.push(child);
                        if (uName.includes("TB")) boxTB.expandByObject(child), hasTB = true;
                        else if (uName.includes("TA")) boxTA.expandByObject(child), hasTA = true;
                    }
                }
            });

            const portalsGroup = new THREE.Group();
            if (hasTA) {
                const cA = boxTA.getCenter(new THREE.Vector3());
                const sTA = createPortalMarker("TA"); sTA.position.set(cA.x, boxTA.max.y + 8.5, boxTA.min.z - 4.0);
                portalsGroup.add(sTA);
            }
            if (hasTB) {
                const cB = boxTB.getCenter(new THREE.Vector3());
                const sTB = createPortalMarker("TB"); sTB.position.set(cB.x, boxTB.max.y + 8.5, boxTB.min.z - 4.0);
                portalsGroup.add(sTB);
            }
            scene.add(portalsGroup);

            if (payload.showMeters && tunnelMeshes.length > 0) {
                const overallBox = new THREE.Box3();
                tunnelMeshes.forEach(tm => overallBox.expandByObject(tm));
                const size = overallBox.getSize(new THREE.Vector3());
                const rulerGroup = new THREE.Group();
                const isZAxis = size.z >= size.x;
                const lengthM = isZAxis ? size.z : size.x;
                const startCoord = isZAxis ? overallBox.min.z : overallBox.min.x;
                const endCoord = isZAxis ? overallBox.max.z : overallBox.max.x;
                const step = 10.0; const stepsCount = Math.floor(lengthM / step);
                const yRuler = overallBox.min.y - 0.2;
                const lateralPos = isZAxis ? (overallBox.max.x + 3.5) : (overallBox.max.z + 3.5);

                const linePoints = isZAxis ? [new THREE.Vector3(lateralPos, yRuler, startCoord), new THREE.Vector3(lateralPos, yRuler, endCoord)]
                                           : [new THREE.Vector3(startCoord, yRuler, lateralPos), new THREE.Vector3(endCoord, yRuler, lateralPos)];
                const axisGeom = new THREE.BufferGeometry().setFromPoints(linePoints);
                const axisMat = new THREE.LineBasicMaterial({ color: 0x00E5FF, linewidth: 3 });
                rulerGroup.add(new THREE.Line(axisGeom, axisMat));

                for (let i = 0; i <= stepsCount; i++) {
                    const curPos = startCoord + i * step;
                    const distTxt = ((stepsCount * step) - (i * step)).toFixed(0) + " m";
                    const tickPts = isZAxis ? [new THREE.Vector3(lateralPos - 0.8, yRuler, curPos), new THREE.Vector3(lateralPos + 0.8, yRuler, curPos)]
                                            : [new THREE.Vector3(curPos, yRuler, lateralPos - 0.8), new THREE.Vector3(curPos, yRuler, lateralPos + 0.8)];
                    rulerGroup.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(tickPts), axisMat));
                    const lbl = createRulerLabel(distTxt);
                    lbl.position.set(isZAxis ? lateralPos + 2.4 : curPos, yRuler + 0.4, isZAxis ? curPos : lateralPos + 2.4);
                    rulerGroup.add(lbl);
                }
                scene.add(rulerGroup);
            }

            const finalSensors = [];
            rawSensors.forEach(child => {
                child.visible = false;
                const sensorId = extractSensorId(child.name);
                const info = checkSensorData(sensorId);
                if (info.found) {
                    const wPos = new THREE.Vector3(); child.getWorldPosition(wPos);
                    finalSensors.push({ mesh: child, pos: wPos, sensorName: info.key, val: info.val });
                }
            });

            let alreadyHighlightedOne = false;
            finalSensors.forEach(item => {
                const isCandidate = (payload.selectedSensor && payload.selectedSensor !== "Seçiniz..." && item.sensorName === payload.selectedSensor);
                const isSelected = isCandidate && !alreadyHighlightedOne;
                if (isSelected) alreadyHighlightedOne = true;

                const detached = new THREE.Mesh(
                    item.mesh.geometry.clone(), 
                    new THREE.MeshBasicMaterial({ color: isSelected ? 0xFFD700 : 0xFFFFFF })
                );
                detached.position.copy(item.pos);
                detached.userData = { sensorName: item.sensorName, val: item.val, isUsable: true };
                sensorScene.add(detached); interactiveSensors.push(detached);
                if (isSelected) { selectedMeshRef = detached; updateHud(item.sensorName, item.val); }
            });

            const R_SENSOR = 60.0;
            tunnelMeshes.forEach(tMesh => {
                const geom = tMesh.geometry; if (!geom.attributes.position) return;
                const posAttr = geom.attributes.position; const colors = new Float32Array(posAttr.count * 3);
                tMesh.updateMatrixWorld(true);

                for (let i = 0; i < posAttr.count; i++) {
                    const worldV = new THREE.Vector3().fromBufferAttribute(posAttr, i).applyMatrix4(tMesh.matrixWorld);
                    let totalWeight = 0, accumulatedVal = 0;

                    for (let s of finalSensors) {
                        const d = worldV.distanceTo(s.pos);
                        if (d < R_SENSOR) {
                            const w = Math.pow(1.0 - (d / R_SENSOR), 1.3) / (Math.pow(d, 0.85) + 0.1);
                            accumulatedVal += s.val * w; totalWeight += w;
                        }
                    }
                    const idx = i * 3;
                    if (totalWeight > 0.00001) {
                        const c = getColorForValue(accumulatedVal / totalWeight, payload.clim);
                        colors[idx] = c.r; colors[idx+1] = c.g; colors[idx+2] = c.b;
                    } else {
                        colors[idx] = 0.08; colors[idx+1] = 0.11; colors[idx+2] = 0.16;
                    }
                }
                geom.setAttribute('color', new THREE.BufferAttribute(colors, 3));
                tMesh.material = new THREE.MeshStandardMaterial({
                    vertexColors: true,
                    roughness: 0.2,
                    metalness: 0.02,
                    transparent: false,
                    depthWrite: true
                });
            });

            const box = new THREE.Box3().setFromObject(model);
            const center = box.getCenter(new THREE.Vector3());
            controls.target.copy(center);
            camera.position.set(center.x - 40, center.y + 45, center.z + 55);
            controls.update();
        });

        function updateHud(name, val) {
            selectedHud.style.display = 'block';
            hudName.innerText = name;
            hudVal.innerText = (val > 0 ? "+" : "") + val.toFixed(2) + " " + payload.unit;
        }

        window.addEventListener('click', function(e) {
            const rect = renderer.domElement.getBoundingClientRect();
            mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
            mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
            raycaster.setFromCamera(mouse, camera);
            const hits = raycaster.intersectObjects(interactiveSensors);
            if (hits.length > 0) {
                const obj = hits[0].object;
                updateHud(obj.userData.sensorName, obj.userData.val);
            }
        });

        function animate(time) {
            requestAnimationFrame(animate); TWEEN.update(time); controls.update();
            renderer.clear(); renderer.render(scene, camera);
            renderer.clearDepth(); renderer.render(sensorScene, camera);
        }
        requestAnimationFrame(animate);
    </script>
</body>
</html>"""

        final_html = raw_template.replace("__INJECT_PAYLOAD__", json_payload).replace("__INJECT_MODEL__", model_b64)
        st.components.v1.html(final_html, height=600, scrolling=False)
