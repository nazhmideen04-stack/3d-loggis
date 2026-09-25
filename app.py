import os
import re
import sys
import csv
import base64
import subprocess
from datetime import datetime
import numpy as np
import pandas as pd
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
    }

    code {
        background-color: transparent !important;
        color: #00C8E6 !important;
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

    div[data-baseweb="select"] {
        background-color: #0E182A !important;
        border: 1px solid rgba(0, 200, 230, 0.4) !important;
        border-radius: 6px !important;
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
    }

    div.stButton > button:hover {
        background-color: #132E4C !important;
        border-color: #00C8E6 !important;
        color: #FFFFFF !important;
    }

    [data-testid="stDataFrame"] {
        background-color: #0E182A !important;
        border-radius: 8px !important;
        padding: 10px !important;
        border: 1px solid rgba(0, 200, 230, 0.3) !important;
    }
</style>
""", unsafe_allow_html=True)

LOGO_B64 = ""
if os.path.exists(LOGO_PATH):
    with open(LOGO_PATH, "rb") as f:
        LOGO_B64 = base64.b64encode(f.read()).decode()

LOGO_TAG = f'<img src="data:image/jpeg;base64,{LOGO_B64}" style="width: 250px; height: auto; display: block; opacity: 0.85; border-radius: 4px;" alt="DESTECH">' if LOGO_B64 else '<span class="destech-badge">DESTECH</span>'

st.markdown(f"""
<div class="header-box" style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-top: -20px; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid rgba(0, 200, 230, 0.15);">
    <div style="display: flex; flex-direction: column; justify-content: center;">
        <h1 style="margin: 0 !important; padding: 0 !important; font-size: 30px !important; line-height: 1.1 !important;">CATERİNG - THY</h1>
        <div style="color: #00C8E6; font-weight: 700; font-size: 13px; letter-spacing: 1.5px; margin-top: 3px;">SENSÖR TAKİP SİSTEMİ & ANALİZ</div>
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

SENSOR_RE = re.compile(r"(?<![A-Za-z0-9])(T[AB]-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)", re.IGNORECASE)

TR_MONTHS = {
    "01": "Ocak", "02": "Şubat", "03": "Mart", "04": "Nisan", "05": "Mayıs", "06": "Haziran",
    "07": "Temmuz", "08": "Ağustos", "09": "Eylül", "10": "Ekim", "11": "Kasım", "12": "Aralık",
}

def clean_num(s):
    if s is None: return np.nan
    if isinstance(s, (int, float, np.integer, np.floating)): return float(s)
    s = str(s).strip()
    if not s: return np.nan
    s = s.replace("\u2212", "-").replace("\u2013", "-")
    s = re.sub(r"[\s\u00a0\u202f\u2009']", "", s)
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."): s = s.replace(".", "").replace(",", ".")
        else: s = s.replace(",", "")
    else: s = s.replace(",", ".")
    m = re.search(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", s)
    return float(m.group()) if m else np.nan

def parse_ts(s):
    if s is None: return None
    t = str(s).replace("\ufeff", "").strip()
    if not t or not re.search(r"\d", t): return None
    t = re.sub(r"\s+", " ", t.replace("T", " "))
    try:
        ts = pd.to_datetime(t, dayfirst=True, errors="coerce")
        if pd.notna(ts): return ts.to_pydatetime().replace(tzinfo=None)
    except Exception: pass
    return None

def ts_key(dt): return dt.strftime("%Y-%m-%d %H:%M:%S")
def fmt_ts(key):
    if not key or key == "-": return "-"
    try: return datetime.strptime(key, "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y %H:%M")
    except ValueError: return str(key)

def extract_sensor_name(header):
    if header is None: return None
    m = SENSOR_RE.search(str(header).replace("\ufeff", ""))
    return m.group(1).strip("-") if m else None

def classify_sensor(name):
    if not name: return None
    segs = name.upper().split("-")[1:]
    if any(s.startswith("CS") for s in segs): return "hoop"
    if any(s.startswith("S") for s in segs): return "axial"
    if any(s.startswith("TP") for s in segs): return "temp"
    return None

def ensure_playwright_installed():
    try: subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    except Exception: pass

def _read_text_any(path):
    with open(path, "rb") as f: raw = f.read()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"): return raw.decode("utf-16", errors="ignore")
    for enc in ("utf-8-sig", "cp1252"):
        try: return raw.decode(enc)
        except UnicodeDecodeError: pass
    return raw.decode("latin-1", errors="ignore")

def parse_loggis_csv(path):
    text = _read_text_any(path).replace("\ufeff", "")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines: return {}
    sample = "\n".join(lines[:5])
    delim = max([";", "\t"], key=sample.count)
    if sample.count(delim) == 0: delim = ","
    rows = list(csv.reader(lines, delimiter=delim))

    header_idx, best_cols = None, []
    for i, row in enumerate(rows[:15]):
        cols = [(j, extract_sensor_name(h)) for j, h in enumerate(row)]
        cols = [(j, n) for j, n in cols if n]
        if len(cols) > len(best_cols): header_idx, best_cols = i, cols
    if header_idx is None: return {}

    out = {}
    for row in rows[header_idx + 1:]:
        dt = None
        for cell in row[:3]:
            dt = parse_ts(cell)
            if dt: break
        if not dt: continue
        vals = {}
        for j, name in best_cols:
            if j < len(row):
                v = clean_num(row[j])
                if not np.isnan(v): vals[name] = v
        if vals: out.setdefault(ts_key(dt), {}).update(vals)
    return out

# ---------------------------------------------------------
# СКАЧИВАНИЕ ПО ТВОЕМУ ТОЧНОМУ СКРИПТУ (ВСЕ 3 CSV ФАЙЛА)
# ---------------------------------------------------------
@st.cache_data(ttl=600, show_spinner=False)
def download_all_csv_data():
    master_db = {k: {} for k in CATEGORIES}
    
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
        )
        context = browser.new_context(accept_downloads=True, viewport={"width": 1920, "height": 1080}, locale="fr-FR")
        page = context.new_page()
        
        try:
            page.goto(URL, timeout=60000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
            
            # Твой точный алгоритм
            page.get_by_role("combobox").first.select_option("ALL")
            page.wait_for_timeout(1500)
            page.get_by_text("Types").click()
            page.wait_for_timeout(1000)
            
            for cat_key, cat_cfg in CATEGORIES.items():
                cat_name = cat_cfg["name"]
                try:
                    page.get_by_role("listbox").select_option(cat_name)
                    page.wait_for_timeout(2000)
                    
                    with page.expect_download(timeout=30000) as download_info:
                        try:
                            with page.expect_popup(timeout=8000) as page1_info:
                                page.get_by_text("🠋CSV").click()
                            page1 = page1_info.value
                            page1.close()
                        except:
                            page.get_by_text("🠋CSV").click()
                    
                    download = download_info.value
                    csv_path = download.path()
                    
                    if csv_path and os.path.exists(csv_path):
                        parsed = parse_loggis_csv(csv_path)
                        for t_key, s_vals in parsed.items():
                            for s_name, val in s_vals.items():
                                if classify_sensor(s_name) == cat_key:
                                    master_db[cat_key].setdefault(t_key, {})[s_name] = val
                except Exception as e:
                    pass
                    
        except Exception as e:
            pass
        finally:
            context.close()
            browser.close()
            
    return master_db

@st.cache_data
def get_model_b64(path):
    if not os.path.exists(path): return None
    with open(path, "rb") as f: return base64.b64encode(f.read()).decode()

col_nav, col_3d = st.columns([1, 4])

with col_nav:
    st.subheader("KONTROL PANELİ")
    
    data_mode = st.radio("Veri Modu Seçimi:", options=["Canlı Veriler", "Arşiv Veriler"])
    selected_comp = st.radio("Görüntülenecek Bileşen (Kategori):", options=["hoop", "axial", "temp"], format_func=lambda k: CATEGORIES[k]["title"])

    target_timestamp = "-"
    latest_timestamp = None
    raw_v_map = {}
    latest_v_map = {}
    cat_cfg = CATEGORIES[selected_comp]
    compare_mode = False
    table_data = []

    with st.spinner("⏳ Данные загружаются с LoggIS по вашему алгоритму..."):
        full_db = download_all_csv_data()

    cat_rows = full_db.get(selected_comp, {})
    cat_dates = sorted([k for k, v in cat_rows.items() if v], reverse=True)

    if not cat_dates:
        st.error("⚠️ Данные категории не найдены. Нажмите 'Verileri Yenile'.")
    else:
        latest_key = cat_dates[0]
        latest_timestamp = fmt_ts(latest_key)

        if data_mode == "Arşiv Veriler":
            st.markdown("---")
            st.subheader("Zaman Seçimi")
            compare_mode = st.checkbox("Karşılaştır (Fark Analizi)")

            date_hierarchy = {}
            for k in cat_dates:
                y, m, d, t = k[0:4], k[5:7], k[8:10], k[11:]
                date_hierarchy.setdefault(y, {}).setdefault(m, {}).setdefault(d, []).append(t)

            years = sorted(date_hierarchy.keys(), reverse=True)
            sel_year = st.selectbox("Yıl Seçiniz", options=years)

            if sel_year:
                months = sorted(date_hierarchy[sel_year].keys(), reverse=True)
                sel_month = st.selectbox("Ay Seçiniz:", options=months, format_func=lambda mm: f"{mm} - {TR_MONTHS.get(mm, mm)}")

                if sel_month:
                    days = sorted(date_hierarchy[sel_year][sel_month].keys(), reverse=True)
                    sel_day = st.selectbox("Gün Seçiniz:", options=days)

                    if sel_day:
                        times = sorted(date_hierarchy[sel_year][sel_month][sel_day], reverse=True)
                        sel_time = st.selectbox("Saat Seçiniz:", options=times, format_func=lambda t: t[:5])

                        if sel_time:
                            target_key = f"{sel_year}-{sel_month}-{sel_day} {sel_time}"
                            target_timestamp = fmt_ts(target_key)
                            raw_v_map = cat_rows.get(target_key, {})
                            latest_v_map = cat_rows.get(latest_key, {})
        else:
            # Для живых данных берем самые свежие данные из скачанного файла
            target_timestamp = latest_timestamp
            raw_v_map = cat_rows.get(latest_key, {})

    if st.button("Verileri Yenile"):
        st.cache_data.clear()
        st.rerun()

# ФИЛЬТРАЦИЯ
active_category_values = {}
if raw_v_map:
    for s_name, val in raw_v_map.items():
        if val is None or np.isnan(val): continue
        if classify_sensor(s_name) == selected_comp:
            if compare_mode:
                latest_val = latest_v_map.get(s_name)
                str_val = f"{float(val):.2f}"
                str_latest = f"{float(latest_val):.2f}" if latest_val is not None and not np.isnan(latest_val) else "-"
                
                if latest_val is not None and not np.isnan(latest_val):
                    delta = float(latest_val) - float(val)
                    active_category_values[s_name] = delta
                    str_delta = f"{delta:+.2f}"
                else:
                    str_delta = "-"
                    
                table_data.append({"Sensör No": s_name, "Arşiv Değeri": str_val, "Güncel Değer": str_latest, "Fark (Δ)": str_delta})
            else:
                active_category_values[s_name] = float(val)

vals = [float(v) for v in active_category_values.values() if not np.isnan(v)]
if not vals:
    clim = [-1.0, 1.0]
else:
    if compare_mode:
        max_abs = max(abs(min(vals)), abs(max(vals)))
        clim = [-round(max_abs * 1.05, 2), round(max_abs * 1.05, 2)] if max_abs >= 0.001 else [-0.5, 0.5]
    else:
        real_min, real_max = float(min(vals)), float(max(vals))
        diff = abs(real_max - real_min)
        clim = [round(real_min - 0.5, 2), round(real_max + 0.5, 2)] if diff < 0.001 else [round(real_min - diff*0.02, 2), round(real_max + diff*0.02, 2)]

with col_nav:
    st.markdown("---")
    st.subheader("GÖRÜNÜМ AYARLARI")
    tunnel_opacity = st.slider("Tünel Opaklığı (%):", min_value=0, max_value=100, value=85, step=5) / 100.0
    show_meters = st.checkbox("Metre Cetveli Göster", value=True)
    show_no_data_red = st.checkbox("⚠️ Verisi Olmayan Sensörleri Göster", value=False)

    st.markdown("---")
    st.write("**Aktif Periyot:**")
    st.markdown(f"<span class='neon-data' style='font-size: 13px;'>{target_timestamp}</span>", unsafe_allow_html=True)
    st.write("**Aktif Sensör Sayısı:**")
    st.markdown(f"<span class='neon-data' style='font-size: 18px;'>{len(active_category_values)}</span>", unsafe_allow_html=True)
    st.write("**Skala Limitleri:**")
    st.markdown(f"<span class='neon-data' style='font-size: 14px;'>Min: {clim[0]:+.2f} | Maks: {clim[1]:+.2f} {cat_cfg['unit']}</span>", unsafe_allow_html=True)

# 3D ОБЛАСТЬ
with col_3d:
    sensor_options = ["Seçiniz..."] + sorted(list(active_category_values.keys()))
    sel_col1, sel_col2 = st.columns([3, 1])
    with sel_col1:
        selected_sensor = st.selectbox("Modelde Sensör Odakla:", options=sensor_options)
    with sel_col2:
        if selected_sensor != "Seçiniz..." and selected_sensor in active_category_values:
            st.metric(label="Değer", value=f"{active_category_values[selected_sensor]:+.2f} {cat_cfg['unit']}")
        else:
            st.metric(label="Değer", value="-")

    model_b64 = get_model_b64(MODEL_PATH)
    if not model_b64:
        st.error(f"⚠️ `{MODEL_PATH}` bulunamadı!")
    else:
        payload_data = {
            "activeCategoryValues": active_category_values, "selectedSensor": selected_sensor,
            "unit": cat_cfg["unit"], "clim": clim, "comp": selected_comp,
            "tunnelOpacity": float(tunnel_opacity), "showMeters": show_meters,
            "showNoDataRed": show_no_data_red, "isCompareMode": compare_mode
        }
        json_payload = json.dumps(payload_data)

        raw_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
        body { margin: 0; padding: 0; overflow: hidden; background-color: #0A0E17; font-family: 'Chakra Petch', sans-serif; touch-action: none; border-radius: 8px; }
        #canvas-container { width: 100%; height: 100vh; position: relative; }
        #sensor-tooltip { position: absolute; display: none; background: rgba(14, 24, 42, 0.95); border: 1px solid #00C8E6; color: #FFFFFF; padding: 6px 12px; border-radius: 6px; font-size: 13px; pointer-events: none; z-index: 100; box-shadow: 0 4px 16px rgba(0, 200, 230, 0.35); }
        #selected-hud { position: absolute; top: 14px; left: 14px; display: none; background: rgba(10, 14, 23, 0.92); border: 1px solid #00C8E6; padding: 8px 14px; border-radius: 8px; z-index: 95; box-shadow: 0 4px 16px rgba(0, 200, 230, 0.3); max-width: 220px; }
        #selected-hud .hud-title { font-size: 11px; color: #8397AD; text-transform: uppercase; letter-spacing: 0.8px; }
        #selected-hud .hud-name { font-size: 15px; color: #FFFFFF; font-weight: 700; margin: 1px 0 3px 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        #selected-hud .hud-val { font-size: 18px; color: #00E5FF; font-weight: 700; }
        #loader { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: #00C8E6; font-size: 16px; font-weight: 700; letter-spacing: 1px; text-align: center; width: 80%; }
        #color-legend { position: absolute; top: 14px; right: 14px; display: flex; flex-direction: column; align-items: center; background: rgba(10, 14, 23, 0.92); padding: 10px 12px; border: 1px solid rgba(0, 200, 230, 0.55); box-shadow: 0 0 16px rgba(0, 200, 230, 0.25); border-radius: 6px; z-index: 90; user-select: none; }
        #legend-title { color: #00E5FF; font-size: 12px; font-weight: 700; margin-bottom: 6px; text-transform: none !important; letter-spacing: 0.5px; }
        .legend-bar-container { display: flex; align-items: stretch; height: 180px; }
        #legend-bar { width: 16px; border-radius: 4px; border: 1px solid rgba(255, 255, 255, 0.35); margin-right: 8px; }
        .legend-labels { display: flex; flex-direction: column; justify-content: space-between; color: #FFFFFF; font-size: 11px; font-weight: 700; }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/tween.js/18.6.4/tween.umd.js"></script>
</head>
<body>
    <div id="canvas-container">
        <div id="loader">3B MODEL YÜKLENİYOR...</div>
        <div id="sensor-tooltip"></div>
        <div id="selected-hud">
            <div class="hud-title">Seçilen Sensör</div>
            <div id="hud-sensor-name" class="hud-name">--</div>
            <div id="hud-sensor-val" class="hud-val">-</div>
        </div>
        <div id="color-legend">
            <div id="legend-title"></div>
            <div class="legend-bar-container">
                <div id="legend-bar"></div>
                <div class="legend-labels">
                    <span id="lbl-max">-</span>
                    <span id="lbl-mid">-</span>
                    <span id="lbl-min">-</span>
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

        let isModelLoaded = false;
        function saveCamState() {
            if (!isModelLoaded) return;
            try { window.sessionStorage.setItem('loggis_cam_v7', JSON.stringify({ pos: camera.position.toArray(), tgt: controls.target.toArray() })); } catch(e) {}
        }

        const hoopStops = [new THREE.Color("#050833"), new THREE.Color("#0044FF"), new THREE.Color("#00D5FF"), new THREE.Color("#00FF66"), new THREE.Color("#FFEE00"), new THREE.Color("#FF7700"), new THREE.Color("#FF0022")];
        const axialStops = [new THREE.Color("#080038"), new THREE.Color("#2A0A5E"), new THREE.Color("#630F78"), new THREE.Color("#9E1B7F"), new THREE.Color("#D32B6E"), new THREE.Color("#F55447"), new THREE.Color("#FF9500")];
        const temperatureStops = [new THREE.Color("#020024"), new THREE.Color("#0033FF"), new THREE.Color("#00D8FF"), new THREE.Color("#00FF44"), new THREE.Color("#B4FF00"), new THREE.Color("#FFDD00"), new THREE.Color("#FF4400"), new THREE.Color("#D50000")];
        const compareStops = [new THREE.Color("#0055FF"), new THREE.Color("#00E5FF"), new THREE.Color("#2E3A59"), new THREE.Color("#FFDD00"), new THREE.Color("#FF0033")];

        let currentStops = hoopStops;
        if (payload.isCompareMode) { currentStops = compareStops; legendTitle.innerText = "Δ Fark [" + payload.unit + "]"; }
        else {
            if (payload.comp === "axial") { currentStops = axialStops; legendTitle.innerText = "Boyuna [" + payload.unit + "]"; }
            else if (payload.comp === "temp") { currentStops = temperatureStops; legendTitle.innerText = "Sıcaklık [" + payload.unit + "]"; }
            else { currentStops = hoopStops; legendTitle.innerText = "Çevresel [" + payload.unit + "]"; }
        }

        function buildExactLegendGradient(stops) {
            const n = stops.length; const items = [];
            for (let i = 0; i < n; i++) { items.push('#' + stops[n - 1 - i].getHexString() + ' ' + ((i / (n - 1)) * 100).toFixed(1) + '%'); }
            return 'linear-gradient(to bottom, ' + items.join(', ') + ')';
        }
        legendBar.style.background = buildExactLegendGradient(currentStops);

        function sampleColorRamp(stops, t) {
            t = Math.max(0.0, Math.min(1.0, t));
            const scaled = t * (stops.length - 1);
            const idx = Math.floor(scaled); const fract = scaled - idx;
            if (idx >= stops.length - 1) return stops[stops.length - 1].clone();
            const c = new THREE.Color(); c.lerpColors(stops[idx], stops[idx + 1], fract);
            return c;
        }

        function getColorForValue(val, clim) {
            if (val === undefined || isNaN(val)) return new THREE.Color(0x08111e);
            return sampleColorRamp(currentStops, (val - clim[0]) / ((clim[1] - clim[0]) || 1.0));
        }

        lblMax.innerText = payload.clim[1].toFixed(2);
        lblMid.innerText = ((payload.clim[0] + payload.clim[1]) / 2).toFixed(2);
        lblMin.innerText = payload.clim[0].toFixed(2);

        const scene = new THREE.Scene(); scene.background = new THREE.Color(0x0A0E17);
        const sensorScene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 5000);
        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.autoClear = false; container.appendChild(renderer.domElement);

        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true; controls.dampingFactor = 0.05;
        controls.minDistance = 0.5; controls.maxDistance = 2500;
        controls.touches = { ONE: THREE.TOUCH.ROTATE, TWO: THREE.TOUCH.DOLLY_PAN };
        controls.addEventListener('change', saveCamState);

        scene.add(new THREE.AmbientLight(0xffffff, 1.4));
        const d1 = new THREE.DirectionalLight(0x00E5FF, 1.6); d1.position.set(60, 100, 80); scene.add(d1);
        const d2 = new THREE.DirectionalLight(0xffffff, 1.0); d2.position.set(-60, -40, -80); scene.add(d2);

        const interactiveSensors = []; const tunnelMeshes = [];
        const raycaster = new THREE.Raycaster(); const mouse = new THREE.Vector2();

        function extractSensorId(name) { const m = name.match(/T[AB]-[A-Za-z0-9\-]+/i); return m ? m[0] : name; }
        function normalizeKey(str) { return String(str).toUpperCase().replace(/[^A-Z0-9]/g, ''); }
        function getCanonicalSensorId(name) {
            const m = name.match(/(T[AB])-([A-Za-z]+)0*(\d+)-([A-Za-z0-9]+)/i);
            if (m) return (m[1] + '-' + m[2] + parseInt(m[3], 10) + '-' + m[4]).toUpperCase();
            return name.toUpperCase();
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

        function createPortalMarker(text) {
            const canvas = document.createElement('canvas'); canvas.width = 2048; canvas.height = 1024; const ctx = canvas.getContext('2d');
            ctx.fillStyle = 'rgba(10, 14, 23, 0.95)'; ctx.strokeStyle = '#00C8E6'; ctx.lineWidth = 56;
            ctx.strokeRect(40, 40, 1968, 944); ctx.fillRect(40, 40, 1968, 944);
            ctx.font = '900 540px Syne, Chakra Petch, sans-serif'; ctx.fillStyle = '#00E5FF'; ctx.shadowColor = '#00C8E6'; ctx.shadowBlur = 72;
            ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(text, 1024, 512);
            const texture = new THREE.CanvasTexture(canvas); const mat = new THREE.SpriteMaterial({ map: texture, depthTest: false });
            return new THREE.Sprite(mat);
        }

        function createRulerLabel(text) {
            const canvas = document.createElement('canvas'); canvas.width = 256; canvas.height = 128; const ctx = canvas.getContext('2d');
            ctx.fillStyle = 'rgba(10, 14, 23, 0.9)'; ctx.strokeStyle = 'rgba(0, 229, 255, 0.85)'; ctx.lineWidth = 5;
            ctx.strokeRect(6, 6, 244, 116); ctx.fillRect(6, 6, 244, 116);
            ctx.font = '700 48px Chakra Petch, sans-serif'; ctx.fillStyle = '#FFFFFF'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(text, 128, 64);
            const texture = new THREE.CanvasTexture(canvas); const mat = new THREE.SpriteMaterial({ map: texture, depthTest: false });
            const sprite = new THREE.Sprite(mat); sprite.scale.set(2.4, 1.2, 1); return sprite;
        }

        const binaryStr = atob(modelB64); const bytes = new Uint8Array(binaryStr.length);
        for (let i = 0; i < binaryStr.length; i++) bytes[i] = binaryStr.charCodeAt(i);
        let selectedMeshRef = null;

        new THREE.GLTFLoader().parse(bytes.buffer, '', function(gltf) {
            const model = gltf.scene; scene.add(model); model.updateMatrixWorld(true); loaderText.style.display = 'none';

            const rawSensors = [];
            model.traverse(function(child) {
                if (child.isLine || child.isLineSegments) { child.visible = false; return; }
                if (child.isMesh) {
                    const name = child.name; const uName = name.toUpperCase();
                    if (uName.includes("BOX001")) { child.visible = false; return; }
                    if (uName.startsWith("TA-") || uName.startsWith("TB-") || uName.includes("-CS") || uName.includes("-S") || uName.includes("-TP")) {
                        rawSensors.push(child);
                    } else if (uName.includes("TUNNEL") || uName.includes("TÜNEL") || uName === "TA" || uName === "TB") {
                        tunnelMeshes.push(child);
                    } else {
                        child.material = new THREE.MeshStandardMaterial({ color: 0x141E2D, roughness: 0.8 });
                    }
                }
            });

            const targetMeshes = [];
            rawSensors.forEach(child => {
                child.visible = false;
                const sensorId = extractSensorId(child.name);
                const dataInfo = checkSensorData(sensorId);
                const wPos = new THREE.Vector3(); child.getWorldPosition(wPos);
                targetMeshes.push({ mesh: child, pos: wPos, sensorName: dataInfo.key, hasData: dataInfo.found, val: dataInfo.val });
            });

            const finalSensors = [];
            targetMeshes.forEach(item => {
                let duplicate = null;
                for (let f of finalSensors) { if (f.pos.distanceTo(item.pos) < 0.12 && getCanonicalSensorId(f.sensorName) === getCanonicalSensorId(item.sensorName)) { duplicate = f; break; } }
                if (!duplicate) finalSensors.push(item);
                else if (!duplicate.hasData && item.hasData) { duplicate.hasData = true; duplicate.val = item.val; duplicate.sensorName = item.sensorName; duplicate.mesh = item.mesh; }
            });

            let alreadyHighlightedOne = false;
            finalSensors.forEach(item => {
                if (item.hasData || payload.showNoDataRed) {
                    const isCandidate = (payload.selectedSensor && payload.selectedSensor !== "Seçiniz..." && item.sensorName === payload.selectedSensor);
                    const isSelected = isCandidate && !alreadyHighlightedOne;
                    if (isSelected) alreadyHighlightedOne = true;

                    const sensorMat = new THREE.MeshBasicMaterial({ color: isSelected ? 0xFFD700 : (item.hasData ? 0xFFFFFF : 0xFF0033), side: THREE.DoubleSide });
                    const wQuat = new THREE.Quaternion(); const wScale = new THREE.Vector3();
                    item.mesh.getWorldQuaternion(wQuat); item.mesh.getWorldScale(wScale);
                    const detachedMesh = new THREE.Mesh(item.mesh.geometry.clone(), sensorMat);
                    detachedMesh.position.copy(item.pos); detachedMesh.quaternion.copy(wQuat); detachedMesh.scale.copy(wScale);
                    detachedMesh.userData.sensorName = item.sensorName; detachedMesh.userData.val = item.hasData ? item.val : NaN; detachedMesh.userData.isUsable = item.hasData;
                    sensorScene.add(detachedMesh); interactiveSensors.push(detachedMesh);
                    if (isSelected) { selectedMeshRef = detachedMesh; updateHud(item.sensorName, item.val, item.hasData); }
                }
            });

            const interpolationSensors = interactiveSensors.filter(s => s.userData.isUsable).map(s => ({ pos: s.position.clone(), val: s.userData.val }));
            const R_SENSOR = 60.0;

            tunnelMeshes.forEach(tMesh => {
                const geom = tMesh.geometry; if (!geom || !geom.attributes || !geom.attributes.position) return;
                const posAttr = geom.attributes.position; const colors = new Float32Array(posAttr.count * 3);
                const localV = new THREE.Vector3(); const worldV = new THREE.Vector3();
                tMesh.updateMatrixWorld(true);

                for (let i = 0; i < posAttr.count; i++) {
                    localV.fromBufferAttribute(posAttr, i); worldV.copy(localV).applyMatrix4(tMesh.matrixWorld);
                    let totalWeight = 0, accumulatedVal = 0;
                    for (let s of interpolationSensors) {
                        const d = worldV.distanceTo(s.pos);
                        if (d < R_SENSOR) {
                            const w = Math.pow(1.0 - (d / R_SENSOR), 1.3) / (Math.pow(d, 0.85) + 0.1);
                            accumulatedVal += s.val * w; totalWeight += w;
                        }
                    }
                    const idx = i * 3;
                    if (totalWeight > 0.00001) {
                        const c = getColorForValue(accumulatedVal / totalWeight, payload.clim);
                        colors[idx] = c.r; colors[idx + 1] = c.g; colors[idx + 2] = c.b;
                    } else {
                        colors[idx] = 0.08; colors[idx + 1] = 0.11; colors[idx + 2] = 0.16;
                    }
                }
                geom.setAttribute('color', new THREE.BufferAttribute(colors, 3));
                tMesh.material = new THREE.MeshStandardMaterial({ color: 0xffffff, vertexColors: true, transparent: payload.tunnelOpacity < 0.98, opacity: payload.tunnelOpacity, roughness: 0.20, side: THREE.FrontSide });
            });

            # ЛИНЕЙКИ МАСШТАБ 2X С О КОНЧИКА
            if (payload.showMeters) {
                const overallBox = new THREE.Box3(); 
                tunnelMeshes.forEach(tm => overallBox.expandByObject(tm));
                if (!overallBox.isEmpty()) {
                    const size = overallBox.getSize(new THREE.Vector3()); const rulerGroup = new THREE.Group();
                    const scale = 2.0; const isZAxis = size.z >= size.x; 
                    const length3D = isZAxis ? size.z : size.x; 
                    const startCoord = isZAxis ? overallBox.min.z : overallBox.min.x; 
                    const endCoord = isZAxis ? overallBox.max.z : overallBox.max.x;
                    const stepReal = 10.0; const step3D = stepReal * scale; const stepsCount = Math.floor(length3D / step3D); 
                    const yRuler = overallBox.min.y - 0.2; 
                    const lat1 = isZAxis ? (overallBox.max.x + (3.5 * scale)) : (overallBox.max.z + (3.5 * scale));
                    const lat2 = isZAxis ? (overallBox.min.x - (3.5 * scale)) : (overallBox.min.z - (3.5 * scale));

                    const lp1 = [], lp2 = [];
                    if (isZAxis) { lp1.push(new THREE.Vector3(lat1, yRuler, startCoord), new THREE.Vector3(lat1, yRuler, endCoord)); lp2.push(new THREE.Vector3(lat2, yRuler, startCoord), new THREE.Vector3(lat2, yRuler, endCoord)); }
                    else { lp1.push(new THREE.Vector3(startCoord, yRuler, lat1), new THREE.Vector3(endCoord, yRuler, lat1)); lp2.push(new THREE.Vector3(startCoord, yRuler, lat2), new THREE.Vector3(endCoord, yRuler, lat2)); }

                    const axisMat = new THREE.LineBasicMaterial({ color: 0x00E5FF });
                    rulerGroup.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(lp1), axisMat));
                    rulerGroup.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(lp2), axisMat));

                    for (let i = 0; i <= stepsCount; i++) {
                        const cur3D = endCoord - (i * step3D); const dText = (i * stepReal).toFixed(0) + " m";
                        const tp1 = [];
                        if (isZAxis) tp1.push(new THREE.Vector3(lat1 - 0.8*scale, yRuler, cur3D), new THREE.Vector3(lat1 + 0.8*scale, yRuler, cur3D));
                        else tp1.push(new THREE.Vector3(cur3D, yRuler, lat1 - 0.8*scale), new THREE.Vector3(cur3D, yRuler, lat1 + 0.8*scale));
                        rulerGroup.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(tp1), axisMat));
                        
                        const lbl = createRulerLabel(dText); lbl.scale.set(2.4*scale, 1.2*scale, 1);
                        if (isZAxis) lbl.position.set(lat1 + 2.4*scale, yRuler + 0.4, cur3D); else lbl.position.set(cur3D, yRuler + 0.4, lat1 + 2.4*scale);
                        rulerGroup.add(lbl);
                    }
                    scene.add(rulerGroup);
                }
            }

            const lastSelected = sessionStorage.getItem('loggis_sensor_v7');
            const isNewSensor = (payload.selectedSensor && payload.selectedSensor !== "Seçiniz..." && payload.selectedSensor !== lastSelected);

            if (selectedMeshRef && isNewSensor) {
                sessionStorage.setItem('loggis_sensor_v7', payload.selectedSensor);
                isModelLoaded = true;
                flyCameraTo(selectedMeshRef, true);
            } else {
                let cameraRestored = false;
                try {
                    const saved = sessionStorage.getItem('loggis_cam_v7');
                    if (saved) {
                        const st = JSON.parse(saved);
                        camera.position.fromArray(st.pos); controls.target.fromArray(st.tgt); controls.update(); cameraRestored = true;
                    }
                } catch(e) {}
                
                if (!cameraRestored) {
                    const box = new THREE.Box3().setFromObject(model);
                    const center = box.getCenter(new THREE.Vector3()); const maxDim = Math.max(box.getSize(new THREE.Vector3()).x, box.getSize(new THREE.Vector3()).y, box.getSize(new THREE.Vector3()).z, 20.0);
                    controls.target.copy(center);
                    camera.position.set(center.x - maxDim * 0.1, center.y + maxDim * 0.1, center.z + Math.abs(maxDim / Math.sin(camera.fov * Math.PI / 360)) * 0.25);
                    controls.update();
                }
                isModelLoaded = true;
                saveCamState();
            }
        });

        function updateHud(name, val, isUsable) {
            selectedHud.style.display = 'block'; hudName.innerText = name;
            hudVal.innerText = (isUsable && !isNaN(val)) ? ((val > 0 ? "+" : "") + val.toFixed(2) + " " + payload.unit) : "-";
            hudVal.style.color = isUsable ? "#00E5FF" : "#FF0033";
        }

        function flyCameraTo(targetMesh) {
            const targetPos = targetMesh.position.clone();
            const endCamPos = targetPos.clone().add(new THREE.Vector3(targetPos.x, 0, targetPos.z).normalize().multiplyScalar(4.0)).add(new THREE.Vector3(0, 1.8, 0));
            new TWEEN.Tween(controls.target).to(targetPos, 1400).easing(TWEEN.Easing.Cubic.InOut).start();
            new TWEEN.Tween(camera.position).to(endCamPos, 1400).easing(TWEEN.Easing.Cubic.InOut).onUpdate(() => controls.update()).onComplete(saveCamState).start();
        }

        window.addEventListener('click', function(e) {
            const rect = renderer.domElement.getBoundingClientRect();
            mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1; mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
            raycaster.setFromCamera(mouse, camera); const intersects = raycaster.intersectObjects(interactiveSensors, true);
            if (intersects.length > 0) {
                let obj = intersects[0].object; while (obj && !obj.userData.sensorName && obj.parent) obj = obj.parent;
                if (obj && obj.userData.sensorName) {
                    interactiveSensors.forEach(m => m.material.color.setHex(m === obj ? 0xFFD700 : (m.userData.isUsable ? 0xFFFFFF : 0xFF0033)));
                    flyCameraTo(obj); updateHud(obj.userData.sensorName, obj.userData.val, obj.userData.isUsable);
                }
            }
        });

        window.addEventListener('resize', function() { camera.aspect = container.clientWidth / container.clientHeight; camera.updateProjectionMatrix(); renderer.setSize(container.clientWidth, container.clientHeight); });
        (function animate(time) { requestAnimationFrame(animate); TWEEN.update(time); controls.update(); renderer.clear(); renderer.render(scene, camera); renderer.clearDepth(); renderer.render(sensorScene, camera); })();
    </script>
</body>
</html>"""
        final_html = raw_template.replace("__INJECT_PAYLOAD__", json_payload).replace("__INJECT_MODEL__", model_b64)
        st.components.v1.html(final_html, height=600, scrolling=False)

# Аналитическая таблица
if compare_mode and table_data:
    st.markdown("---")
    st.markdown(f"### Fark Raporu ({target_timestamp} ➔ {latest_timestamp})")
    df = pd.DataFrame(table_data).sort_values(by="Sensör No").reset_index(drop=True)
    st.dataframe(df, use_container_width=True, hide_index=True, height=400)
