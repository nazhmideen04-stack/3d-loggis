import os
import re
import sys
import json
import base64
import subprocess
from datetime import datetime
import numpy as np
import pandas as pd
import streamlit as st
from playwright.sync_api import sync_playwright

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
<div class="header-box" style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-top: -20px; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px стоп rgba(0, 200, 230, 0.15);">
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

def clean_num(s):
    if not s: return np.nan
    s = str(s).replace(",", ".").replace(" ", "").strip()
    m = re.search(r"[-+]?\d+(?:\.\d+)?", s)
    return float(m.group()) if m else np.nan

def ensure_playwright_installed():
    try: subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    except Exception: pass

# ---------------------------------------------------------
# РАДИКАЛЬНЫЙ СБОР ВСЕХ ДАННЫХ ЧЕРЕЗ СКАЧИВАНИЕ CSV ФАЙЛОВ
# ---------------------------------------------------------
@st.cache_data(ttl=300)
def fetch_all_data_via_csv():
    master_db = {k: {} for k in CATEGORIES}
    dates_set = set()

    with sync_playwright() as p:
        browser_args = [
            "--no-sandbox", "--disable-setuid-sandbox",
            "--disable-dev-shm-usage", "--disable-gpu", "--window-size=1920,1080"
        ]
        try: browser = p.chromium.launch(headless=True, args=browser_args)
        except:
            ensure_playwright_installed()
            browser = p.chromium.launch(headless=True, args=browser_args)

        context = browser.new_context(
            accept_downloads=True, viewport={"width": 1920, "height": 1080},
            timezone_id="Europe/Istanbul", locale="fr-FR",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            page.goto(URL, timeout=60000, wait_until="domcontentloaded")
            page.wait_for_timeout(4000)

            # Выбираем режим ALL для максимальной полноты данных
            try: page.get_by_role("combobox").first.select_option("ALL", timeout=5000)
            except: pass
            page.wait_for_timeout(1500)

            try: page.get_by_text("Types").click(timeout=5000)
            except: pass
            page.wait_for_timeout(1000)

            for cat_key, cat_cfg in CATEGORIES.items():
                target_tag = cat_cfg["tag"]
                cat_name = cat_cfg["name"]

                try:
                    page.get_by_role("listbox").select_option(cat_name, timeout=5000)
                except:
                    try: page.locator(f"option:has-text('{cat_name}')").first.click(force=True, timeout=3000)
                    except: pass
                
                page.wait_for_timeout(4000)

                csv_path = None
                try:
                    with page.expect_download(timeout=30000) as download_info:
                        with page.expect_popup(timeout=8000) as page1_info:
                            page.get_by_text("🠋CSV").click(force=True)
                        try:
                            page1 = page1_info.value
                            page1.close()
                        except: pass
                    csv_path = download_info.value.path()
                except Exception as e:
                    pass

                if csv_path and os.path.exists(csv_path):
                    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                    
                    if len(lines) > 2:
                        header = [h.replace('﻿', '').strip() for h in lines[0].strip().split(';')]
                        for line in lines[2:]:
                            parts = [p.strip() for p in line.strip().split(';')]
                            if len(parts) == len(header):
                                date_str = parts[0]
                                if date_str: dates_set.add(date_str)
                                        
                                val_map = {}
                                for h, v_str in zip(header[1:], parts[1:]):
                                    match_cond = False
                                    if target_tag == '-CS' and '-CS' in h: match_cond = True
                                    elif target_tag == '-S' and '-S' in h and '-CS' not in h: match_cond = True
                                    elif target_tag == '-TP' and '-TP' in h and '-CS' not in h and '-S' not in h: match_cond = True

                                    if match_cond or target_tag in h:
                                        if target_tag == "-S" and "-CS" in h: continue
                                        if target_tag == "-TP" and ('-CS' in h or '-S' in h): continue
                                        m = re.search(r"(T[AB]-[A-Za-z0-9\-]+)", h)
                                        s_name = m.group(1) if m else h.split()[0].strip()
                                        v = clean_num(v_str)
                                        if not np.isnan(v):
                                            val_map[s_name] = v
                                master_db[cat_key][date_str] = val_map

        except Exception as e:
            st.warning(f"LoggIS veri hatası: {e}")
        finally:
            browser.close()

    sorted_dates = sorted(list(dates_set), reverse=True)
    return sorted_dates, master_db

@st.cache_data
def get_model_b64(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

col_nav, col_3d = st.columns([1, 4])

with col_nav:
    st.subheader("KONTROL PANELİ")
    
    data_mode = st.radio(
        "Veri Modu Seçimi:",
        options=["Canlı Veriler", "Arşiv Veriler"]
    )

    selected_comp = st.radio(
        "Görüntülenecek Bileşen (Kategori):",
        options=["hoop", "axial", "temp"],
        format_func=lambda k: CATEGORIES[k]["title"]
    )

    target_timestamp = "-"
    latest_timestamp = None
    raw_v_map = {}
    latest_v_map = {}
    cat_cfg = CATEGORIES[selected_comp]
    compare_mode = False
    table_data = []

    with st.spinner("⏳ Загрузка всех данных с сервера LoggIS..."):
        all_dates, full_db = fetch_all_data_via_csv()

    if not all_dates:
        st.error("⚠️ Данные не получены. Проверьте соединение.")
    else:
        latest_timestamp = all_dates[0]

        if data_mode == "Arşiv Veriler":
            st.markdown("---")
            st.subheader("Zaman SeçİMİ")
            compare_mode = st.checkbox("Karşılaştır (Fark Analizi)")

            date_hierarchy = {}
            for d_str in all_dates:
                clean_d = d_str.replace("-", "/")
                if " " in clean_d:
                    date_part, time_part = clean_d.split(" ", 1)
                    parts = date_part.split("/")
                    if len(parts) == 3:
                        y, m, d = parts[0], parts[1], parts[2]
                        date_hierarchy.setdefault(y, {}).setdefault(m, {}).setdefault(d, []).append(time_part)

            years = sorted(list(date_hierarchy.keys()), reverse=True)
            sel_year = st.selectbox("Yıl Seçiniz", options=years)

            if sel_year:
                months = sorted(list(date_hierarchy[sel_year].keys()), reverse=True)
                sel_month = st.selectbox("Ay Seçiniz:", options=months)

                if sel_month:
                    days = sorted(list(date_hierarchy[sel_year][sel_month].keys()), reverse=True)
                    sel_day = st.selectbox("Gün Seçiniz:", options=days)

                    if sel_day:
                        times = sorted(date_hierarchy[sel_year][sel_month][sel_day], reverse=True)
                        sel_time = st.selectbox("Saat Seçiniz:", options=times)

                        if sel_time:
                            target_timestamp = f"{sel_year}/{sel_month}/{sel_day} {sel_time}"
                            raw_v_map = full_db[selected_comp].get(target_timestamp, {})
                            latest_v_map = full_db[selected_comp].get(latest_timestamp, {})
        else:
            target_timestamp = latest_timestamp
            raw_v_map = full_db[selected_comp].get(target_timestamp, {})

    if st.button("Verileri Yenile"):
        st.cache_data.clear()
        st.rerun()

# ФИЛЬТРАЦИЯ
active_category_values = {}
if raw_v_map:
    for s_name, val in raw_v_map.items():
        if val is None or np.isnan(val): continue
        u_name = s_name.upper()
        
        is_valid_sensor = False
        if selected_comp == "hoop" and "-CS" in u_name: is_valid_sensor = True
        elif selected_comp == "axial" and "-S" in u_name and "-CS" not in u_name: is_valid_sensor = True
        elif selected_comp == "temp" and "-TP" in u_name and "-CS" not in u_name and "-S" not in u_name: is_valid_sensor = True

        if is_valid_sensor:
            if compare_mode:
                latest_val = latest_v_map.get(s_name)
                str_val = f"{float(val):.2f}"
                str_latest = f"{float(latest_val):.2f}" if latest_val is not None and not np.isnan(latest_val) else "-"
                
                if latest_val is not None and not np.isnan(latest_val):
                    delta = float(latest_val) - float(val)
                    active_category_values[s_name] = delta
                table_data.append({"Sensör No": s_name, "Arşiv Değeri": str_val, "Günцел Değer": str_latest})
            else:
                active_category_values[s_name] = float(val)

vals = [float(v) for v in active_category_values.values() if not np.isnan(v)]
if not vals:
    clim = [-1.0, 1.0]
else:
    real_min = float(min(vals))
    real_max = float(max(vals))
    diff = abs(real_max - real_min)
    if diff < 0.001: clim = [round(real_min - 0.5, 2), round(real_max + 0.5, 2)]
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
    st.markdown(f"<span class='neon-data' style='font-size: 13px;'>{target_timestamp}</span>", unsafe_allow_html=True)
    st.write("**Aktif Sensör Sayısı:**")
    st.markdown(f"<span class='neon-data' style='font-size: 18px;'>{len(active_category_values)}</span>", unsafe_allow_html=True)

# 3B ОБЛАСТЬ
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
        st.error(f"⚠️ `{MODEL_PATH}` bulunamadы!")
    else:
        payload_data = {
            "activeCategoryValues": active_category_values,
            "selectedSensor": selected_sensor,
            "unit": cat_cfg["unit"],
            "clim": clim,
            "comp": selected_comp,
            "tunnelOpacity": float(tunnel_opacity),
            "showMeters": show_meters,
            "showNoDataRed": show_no_data_red,
            "isCompareMode": compare_mode
        }
        json_payload = json.dumps(payload_data)

        raw_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { margin: 0; padding: 0; overflow: hidden; background-color: #0A0E17; font-family: 'Chakra Petch', sans-serif; }
        #canvas-container { width: 100%; height: 100vh; position: relative; }
        #sensor-tooltip { position: absolute; display: none; background: rgba(14, 24, 42, 0.95); border: 1px solid #00C8E6; color: #FFFFFF; padding: 6px 12px; border-radius: 6px; font-size: 13px; pointer-events: none; z-index: 100; }
        #selected-hud { position: absolute; top: 14px; left: 14px; display: none; background: rgba(10, 14, 23, 0.92); border: 1px solid #00C8E6; padding: 8px 14px; border-radius: 8px; z-index: 95; }
        #loader { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: #00C8E6; font-size: 16px; font-weight: 700; }
        #color-legend { position: absolute; top: 14px; right: 14px; display: flex; flex-direction: column; align-items: center; background: rgba(10, 14, 23, 0.92); padding: 10px 12px; border: 1px solid rgba(0, 200, 230, 0.55); border-radius: 6px; z-index: 90; }
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
            <div id="hud-sensor-name" style="color:#FFF; font-weight:700;">--</div>
            <div id="hud-sensor-val" style="color:#00E5FF; font-weight:700;">-</div>
        </div>
        <div id="color-legend">
            <div id="legend-bar" style="height:180px;"></div>
        </div>
    </div>
    <script>
        const payload = __INJECT_PAYLOAD__;
        const modelB64 = "__INJECT_MODEL__";
        const container = document.getElementById('canvas-container');
        document.getElementById('loader').style.display = 'none';
        
        const scene = new THREE.Scene(); scene.background = new THREE.Color(0x0A0E17);
        const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 5000);
        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        container.appendChild(renderer.domElement);
        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        
        scene.add(new THREE.AmbientLight(0xffffff, 1.4));
        
        const binaryStr = atob(modelB64); const bytes = new Uint8Array(binaryStr.length);
        for (let i = 0; i < binaryStr.length; i++) bytes[i] = binaryStr.charCodeAt(i);

        new THREE.GLTFLoader().parse(bytes.buffer, '', function(gltf) {
            scene.add(gltf.scene);
            const box = new THREE.Box3().setFromObject(gltf.scene);
            const center = box.getCenter(new THREE.Vector3());
            controls.target.copy(center);
            camera.position.set(center.x, center.y + 100, center.z + 200);
            controls.update();
        });

        function animate(time) {
            requestAnimationFrame(animate);
            TWEEN.update(time);
            controls.update();
            renderer.render(scene, camera);
        }
        requestAnimationFrame(animate);
    </script>
</body>
</html>"""
        final_html = raw_template.replace("__INJECT_PAYLOAD__", json_payload).replace("__INJECT_MODEL__", model_b64)
        st.components.v1.html(final_html, height=600, scrolling=False)
