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

st.set_page_config(page_title="CATERİNG - THY", layout="wide")

URL = "https://loggis2.com/?company-id=20ce6d9f-398b-43b3-a452-3580dae39122&project-id=2d381d12-d966-4c90-a7c8-c90d6f758ae0&token-id=6e73d15f-0b2f-4d93-a152-3464f7450e50"

LOGO_PATH = "logo.jpg" if os.path.exists("logo.jpg") else "logo.png"
MODEL_PATH = "tunnel_model.glb"

# Фирменный стиль DESTECH
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;600;700&family=Syne:wght@700;800&display=swap');

    :root {
        --primary-color: #00C8E6 !important;
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

    div[data-testid="stRadio"] > label {
        font-family: 'Chakra Petch', sans-serif !important;
        font-size: 14px !important;
        color: #8397AD !important;
        font-weight: 600 !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] label p {
        font-family: 'Chakra Petch', sans-serif !important;
        font-size: 19px !important;
        color: #E6F0FA !important;
        font-weight: 600 !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) div:first-child {
        filter: hue-rotate(185deg) saturate(2) !important;
        transform: scale(1.2) !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] > label {
        margin-bottom: 14px !important;
        cursor: pointer !important;
        display: flex !important;
        align-items: center !important;
    }

    div[data-baseweb="select"] {
        background-color: #0E182A !important;
        border: 1px solid rgba(0, 200, 230, 0.4) !important;
        border-radius: 6px !important;
    }

    .destech-badge {
        font-family: 'Syne', sans-serif;
        font-size: 16px;
        font-weight: 800;
        letter-spacing: 2px;
        background: #00C8E6;
        color: #000000;
        padding: 6px 18px;
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
        transition: background-color 0.2s ease, border-color 0.2s ease !important;
    }

    div.stButton > button:hover {
        background-color: #132E4C !important;
        border-color: #00C8E6 !important;
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

LOGO_B64 = ""
if os.path.exists(LOGO_PATH):
    with open(LOGO_PATH, "rb") as f:
        LOGO_B64 = base64.b64encode(f.read()).decode()

LOGO_TAG = f'<img src="data:image/jpeg;base64,{LOGO_B64}" style="width: 200px; height: auto; display: block; opacity: 0.85; border-radius: 4px;" alt="DESTECH">' if LOGO_B64 else '<span class="destech-badge">DESTECH</span>'

st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-top: -20px; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid rgba(0, 200, 230, 0.15);">
    <div style="display: flex; flex-direction: column; justify-content: center;">
        <h1 style="margin: 0 !important; padding: 0 !important; font-size: 32px !important; line-height: 1.1 !important;">CATERİNG - THY</h1>
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
def fetch_all_categories_data():
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

        page.goto(URL, timeout=60000, wait_until="domcontentloaded")
        page.wait_for_timeout(3500)

        page.get_by_text("Types").click()
        page.wait_for_timeout(800)

        try:
            page.get_by_role("combobox").first.select_option("MONTH_02")
        except Exception:
            pass
        page.wait_for_timeout(600)

        try:
            page.get_by_role("combobox").nth(1).select_option("TABLE_ROW_DATE")
        except Exception:
            pass
        page.wait_for_timeout(800)

        for cat_key, cat_cfg in CATEGORIES.items():
            try:
                page.get_by_role("listbox").select_option(cat_cfg["name"])
            except Exception:
                try:
                    page.locator(f"option:has-text('{cat_cfg['name']}')").first.click(force=True)
                except Exception:
                    page.get_by_text(cat_cfg["name"]).first.click(force=True)

            page.wait_for_timeout(2500)

            val_map = {}
            latest_date_str = ""

            for _ in range(15):
                extracted = page.evaluate("""() => {
                    const table = document.querySelector('table');
                    if (!table) return null;

                    const trs = Array.from(table.querySelectorAll('tr'));
                    let headerCells = [];
                    for (const tr of trs) {
                        const cells = Array.from(tr.querySelectorAll('th, td')).map(c => c.innerText.trim());
                        if (cells.some(c => c.includes('TA-') || c.includes('TB-'))) {
                            headerCells = cells;
                            break;
                        }
                    }
                    if (headerCells.length === 0 && trs.length > 0) {
                        headerCells = Array.from(trs[0].querySelectorAll('th, td')).map(c => c.innerText.trim());
                    }

                    const tbody = table.querySelector('tbody') || table;
                    const rows = Array.from(tbody.querySelectorAll('tr'));
                    let dataCells = [];
                    for (const r of rows) {
                        const cells = Array.from(r.querySelectorAll('td')).map(c => c.innerText.trim());
                        if (cells.length > 1 && (cells[0].includes('/') || cells[0].includes(':') || cells[0].includes('-'))) {
                            dataCells = cells;
                            break;
                        }
                    }

                    if (headerCells.length === 0 || dataCells.length === 0) return null;
                    return { headers: headerCells, values: dataCells };
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

                page.wait_for_timeout(500)

            all_results[cat_key] = {"values": val_map, "date": latest_date_str}

        browser.close()

    return all_results

@st.cache_data
def get_model_b64(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

col_nav, col_3d = st.columns([1, 4])

with st.spinner("Tüm sensör verileri LoggIS üzerinden alınıyor..."):
    all_data = fetch_all_categories_data()

with col_nav:
    st.subheader("KONTROL PANELİ")
    selected_comp = st.radio(
        "Görüntülenecek Bileşen:",
        options=["hoop", "axial", "temp"],
        format_func=lambda k: CATEGORIES[k]["title"]
    )

    if st.button("Verileri Yenile"):
        st.cache_data.clear()
        st.rerun()

cat_cfg = CATEGORIES[selected_comp]
cur_layer = all_data.get(selected_comp, {"values": {}, "date": ""})
raw_v_map = cur_layer["values"]

active_category_values = {}
for s_name, val in raw_v_map.items():
    if val is None or np.isnan(val):
        continue
    u_name = s_name.upper()
    if selected_comp == "hoop" and "-CS" in u_name:
        active_category_values[s_name] = float(val)
    elif selected_comp == "axial" and ("-S" in u_name) and ("-CS" not in u_name):
        active_category_values[s_name] = float(val)
    elif selected_comp == "temp" and "-TP" in u_name:
        active_category_values[s_name] = float(val)

# Реальный диапазон шкалы
vals = [float(v) for v in active_category_values.values() if not np.isnan(v)]
if not vals:
    clim = [0.0, 1.0]
else:
    real_min = float(min(vals))
    real_max = float(max(vals))
    if abs(real_max - real_min) < 0.001:
        clim = [round(real_min - 1.0, 1), round(real_max + 1.0, 1)]
    else:
        clim = [round(real_min, 1), round(real_max, 1)]

with col_nav:
    st.markdown("---")
    st.subheader("GÖRÜNÜM AYARLARI")
    tunnel_opacity = st.slider("Tünel Opaklığı (%):", min_value=0, max_value=100, value=85, step=5) / 100.0
    show_meters = st.checkbox("Metre Cetveli Göster", value=True)
    show_no_data_red = st.checkbox("⚠️ Verisi Olmayan Sensörleri Göster (Parlak Kırmızı)", value=False)

    st.markdown("---")
    st.write("**En Son Veri Zamanı:**")
    st.markdown(f"<span class='neon-data' style='font-size: 16px;'>{cur_layer['date'] if cur_layer['date'] else 'Bilinmiyor'}</span>", unsafe_allow_html=True)
    
    st.write("**Aktif Sensör Sayısı:**")
    st.markdown(f"<span class='neon-data' style='font-size: 20px;'>{len(active_category_values)}</span>", unsafe_allow_html=True)
    
    st.write("**Skala Limitleri (Gerçek Min / Maks):**")
    st.markdown(f"<span class='neon-data' style='font-size: 15px;'>Min: {clim[0]:+.1f} | Maks: {clim[1]:+.1f} {cat_cfg['unit']}</span>", unsafe_allow_html=True)

    st.markdown("---")
    sensor_options = ["Seçiniz..."] + sorted(list(active_category_values.keys()))
    selected_sensor = st.selectbox("Sensör Değerini İncele:", options=sensor_options)

    if selected_sensor != "Seçiniz..." and selected_sensor in active_category_values:
        st.metric(
            label=f"Seçilen: {selected_sensor}",
            value=f"{active_category_values[selected_sensor]:+.2f} {cat_cfg['unit']}"
        )

# --- 3B THREE.JS ОБЛАСТЬ ---
with col_3d:
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

        threejs_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    overflow: hidden;
                    background-color: #0A0E17;
                    font-family: 'Chakra Petch', sans-serif;
                }}
                #canvas-container {{
                    width: 100vw;
                    height: 100vh;
                    position: relative;
                }}
                #sensor-tooltip {{
                    position: absolute;
                    display: none;
                    background: rgba(14, 24, 42, 0.95);
                    border: 1px solid #00C8E6;
                    color: #FFFFFF;
                    padding: 8px 14px;
                    border-radius: 6px;
                    font-size: 14px;
                    pointer-events: none;
                    z-index: 100;
                    box-shadow: 0 6px 18px rgba(0, 200, 230, 0.35);
                }}
                #selected-hud {{
                    position: absolute;
                    top: 24px;
                    left: 24px;
                    display: none;
                    background: rgba(10, 14, 23, 0.92);
                    border: 1px solid #00C8E6;
                    padding: 12px 18px;
                    border-radius: 8px;
                    z-index: 95;
                    box-shadow: 0 4px 20px rgba(0, 200, 230, 0.3);
                }}
                #selected-hud .hud-title {{
                    font-size: 12px;
                    color: #8397AD;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }}
                #selected-hud .hud-name {{
                    font-size: 18px;
                    color: #FFFFFF;
                    font-weight: 700;
                    margin: 2px 0 6px 0;
                }}
                #selected-hud .hud-val {{
                    font-size: 22px;
                    color: #00E5FF;
                    font-weight: 700;
                }}
                #loader {{
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    color: #00C8E6;
                    font-size: 18px;
                    font-weight: 700;
                    letter-spacing: 1px;
                }}
                #color-legend {{
                    position: absolute;
                    top: 24px;
                    right: 28px;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    background: rgba(10, 14, 23, 0.92);
                    padding: 14px 16px;
                    border: 1px solid rgba(0, 200, 230, 0.55);
                    box-shadow: 0 0 18px rgba(0, 200, 230, 0.25);
                    border-radius: 6px;
                    z-index: 90;
                    user-select: none;
                }}
                #legend-title {{
                    color: #00E5FF;
                    font-size: 14px;
                    font-weight: 700;
                    margin-bottom: 8px;
                    text-transform: none !important;
                    letter-spacing: 0.5px;
                }}
                .legend-bar-container {{
                    display: flex;
                    align-items: stretch;
                    height: 240px;
                }}
                #legend-bar {{
                    width: 20px;
                    border-radius: 4px;
                    border: 1px solid rgba(255, 255, 255, 0.35);
                    margin-right: 10px;
                }}
                .legend-labels {{
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                    color: #FFFFFF;
                    font-size: 12px;
                    font-weight: 700;
                }}
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
                const payload = {json_payload};
                const modelB64 = "{model_b64}";
                
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

                // 1. ПАЛИТРА ДЛЯ ÇEVRESEL GERİNİM (CS) - Яркая Радуга Turbo
                const hoopStops = [
                    new THREE.Color("#0022FF"), // Глубокий синий (мин)
                    new THREE.Color("#00E5FF"), // Циан
                    new THREE.Color("#00FF44"), // Зеленый
                    new THREE.Color("#FFE600"), // Желтый
                    new THREE.Color("#FFAA00"), // Янтарный
                    new THREE.Color("#FF5500"), // Оранжевый
                    new THREE.Color("#FF0022")  // Алый красный (макс)
                ];

                // 2. ПАЛИТРА ДЛЯ BOYUNA GERİNİM (S) - Осевые деформации (Сжатие/Растяжение)
                const axialStops = [
                    new THREE.Color("#081D58"), // Темный индиго (сильное сжатие)
                    new THREE.Color("#253494"), // Синий
                    new THREE.Color("#1D91C0"), // Голубой
                    new THREE.Color("#7FCDBB"), // Аквамарин
                    new THREE.Color("#FFFFD9"), // Нейтрально-светлый
                    new THREE.Color("#FEB24C"), // Персиковый
                    new THREE.Color("#F03B20"), // Оранжево-красный
                    new THREE.Color("#BD0026")  // Насыщенный бордово-красный (сильное растяжение)
                ];

                // 3. ПАЛИТРА ДЛЯ SICAKLIK (TP) - Термографическая температурная шкала
                const tempStops = [
                    new THREE.Color("#000004"), // Угольно-черный (холод)
                    new THREE.Color("#2C105C"), // Глубокий фиолетовый
                    new THREE.Color("#711F81"), // Пурпурный
                    new THREE.Color("#B5367A"), // Маджента
                    new THREE.Color("#F1605D"), // Коралловый
                    new THREE.Color("#FEA066"), // Теплый оранжевый
                    new THREE.Color("#FEDA8B"), // Золотисто-желтый
                    new THREE.Color("#FCFDBF")  // Бело-желтый (жар)
                ];

                // Выбор активной палитры строго по типу
                let currentStops = hoopStops;
                if (payload.comp === "axial") {
                    currentStops = axialStops;
                    legendTitle.innerText = "Boyuna [µm/m]";
                } else if (payload.comp === "temp") {
                    currentStops = tempStops;
                    legendTitle.innerText = "Sıcaklık [°C]";
                } else {
                    currentStops = hoopStops;
                    legendTitle.innerText = "Çevresel [µm/m]";
                }

                // ГЕНЕРАТОР ГРАДИЕНТА СТРОГО ИЗ АКТИВНОГО МАССИВА ЦВЕТОВ THREE.JS
                function buildExactLegendGradient(stops) {
                    const n = stops.length;
                    const items = [];
                    for (let i = 0; i < n; i++) {
                        // Верх легенды — это максимум (i = n - 1), низ — минимум (i = 0)
                        const colorObj = stops[n - 1 - i];
                        const hex = '#' + colorObj.getHexString();
                        const percent = ((i / (n - 1)) * 100).toFixed(1);
                        items.push(hex + ' ' + percent + '%');
                    }
                    return 'linear-gradient(to bottom, ' + items.join(', ') + ')';
                }

                // Применяем полностью синхронизированный градиент для легенды
                legendBar.style.background = buildExactLegendGradient(currentStops);

                function sampleColorRamp(stops, t) {
                    t = Math.max(0, Math.min(1, t));
                    const scaled = t * (stops.length - 1);
                    const idx = Math.floor(scaled);
                    const fract = scaled - idx;
                    if (idx >= stops.length - 1) return stops[stops.length - 1].clone();
                    const c = new THREE.Color();
                    c.lerpColors(stops[idx], stops[idx + 1], fract);
                    return c;
                }

                function getColorForValue(val, clim) {
                    if (val === undefined || isNaN(val)) return new THREE.Color(0x334455);
                    const min = clim[0], max = clim[1];
                    let t = (val - min) / ((max - min) || 1.0);
                    t = Math.max(0, Math.min(1, t));
                    return sampleColorRamp(currentStops, t);
                }

                const scene = new THREE.Scene();
                scene.background = new THREE.Color(0x0A0E17);

                const sensorScene = new THREE.Scene();

                const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 5000);

                const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
                renderer.setSize(container.clientWidth, container.clientHeight);
                renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
                renderer.autoClear = false;
                container.appendChild(renderer.domElement);

                const controls = new THREE.OrbitControls(camera, renderer.domElement);
                controls.enableDamping = true;
                controls.dampingFactor = 0.05;
                controls.minDistance = 0.5;
                controls.maxDistance = 2500;

                controls.addEventListener('change', () => {
                    const camState = {
                        pos: [camera.position.x, camera.position.y, camera.position.z],
                        target: [controls.target.x, controls.target.y, controls.target.z]
                    };
                    sessionStorage.setItem('threejs_camera_state', JSON.stringify(camState));
                });

                const ambientLight = new THREE.AmbientLight(0xffffff, 1.4);
                scene.add(ambientLight);

                const dirLight1 = new THREE.DirectionalLight(0x00E5FF, 1.6);
                dirLight1.position.set(60, 100, 80);
                scene.add(dirLight1);

                const dirLight2 = new THREE.DirectionalLight(0xffffff, 1.0);
                dirLight2.position.set(-60, -40, -80);
                scene.add(dirLight2);

                const interactiveSensors = [];
                const tunnelMeshes = [];
                
                const raycaster = new THREE.Raycaster();
                raycaster.params.Line = { threshold: 1.0 };
                raycaster.params.Points = { threshold: 1.0 };
                
                const mouse = new THREE.Vector2();

                function extractSensorId(name) {
                    const m = name.match(/T[AB]-[A-Za-z0-9\-]+/i);
                    return m ? m[0] : name;
                }

                function normalizeKey(str) {
                    return String(str).toUpperCase().replace(/[^A-Z0-9]/g, '');
                }

                function getCanonicalSensorId(name) {
                    const m = name.match(/(T[AB])-([A-Za-z]+)0*(\d+)-([A-Za-z0-9]+)/i);
                    if (m) {
                        return (m[1] + '-' + m[2] + parseInt(m[3], 10) + '-' + m[4]).toUpperCase();
                    }
                    return name.toUpperCase();
                }

                const normalizedDataMap = {};
                for (const rawKey in payload.activeCategoryValues) {
                    const val = payload.activeCategoryValues[rawKey];
                    normalizedDataMap[rawKey.toUpperCase()] = { canonicalKey: rawKey, val: val };
                    normalizedDataMap[normalizeKey(rawKey)] = { canonicalKey: rawKey, val: val };
                    normalizedDataMap[getCanonicalSensorId(rawKey)] = { canonicalKey: rawKey, val: val };
                }

                function checkSensorData(sensorId, comp) {
                    const uId = sensorId.toUpperCase();
                    const nId = normalizeKey(sensorId);
                    const cId = getCanonicalSensorId(sensorId);

                    if (normalizedDataMap[uId]) return { found: true, key: normalizedDataMap[uId].canonicalKey, val: normalizedDataMap[uId].val };
                    if (normalizedDataMap[cId]) return { found: true, key: normalizedDataMap[cId].canonicalKey, val: normalizedDataMap[cId].val };
                    if (normalizedDataMap[nId]) return { found: true, key: normalizedDataMap[nId].canonicalKey, val: normalizedDataMap[nId].val };

                    if (comp === "temp" && !uId.includes("-TP")) {
                        const tpVariant = uId.replace("-CS", "-TP").replace("-S", "-TP");
                        const cTpVariant = getCanonicalSensorId(tpVariant);
                        if (normalizedDataMap[tpVariant]) return { found: true, key: normalizedDataMap[tpVariant].canonicalKey, val: normalizedDataMap[tpVariant].val };
                        if (normalizedDataMap[cTpVariant]) return { found: true, key: normalizedDataMap[cTpVariant].canonicalKey, val: normalizedDataMap[cTpVariant].val };
                    }

                    return { found: false, key: sensorId, val: NaN };
                }

                function createPortalMarker(text) {
                    const canvas = document.createElement('canvas');
                    canvas.width = 512;
                    canvas.height = 256;
                    const ctx = canvas.getContext('2d');

                    ctx.fillStyle = 'rgba(10, 14, 23, 0.95)';
                    ctx.strokeStyle = '#00C8E6';
                    ctx.lineWidth = 14;
                    ctx.strokeRect(10, 10, 492, 236);
                    ctx.fillRect(10, 10, 492, 236);

                    ctx.font = '900 135px Syne, Chakra Petch, sans-serif';
                    ctx.fillStyle = '#00E5FF';
                    ctx.shadowColor = '#00C8E6';
                    ctx.shadowBlur = 18;
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(text, 256, 128);

                    const texture = new THREE.CanvasTexture(canvas);
                    const mat = new THREE.SpriteMaterial({ map: texture, depthTest: false });
                    const sprite = new THREE.Sprite(mat);
                    sprite.scale.set(6.0, 3.0, 1);
                    return sprite;
                }

                function createRulerLabel(text) {
                    const canvas = document.createElement('canvas');
                    canvas.width = 256;
                    canvas.height = 128;
                    const ctx = canvas.getContext('2d');

                    ctx.fillStyle = 'rgba(10, 14, 23, 0.9)';
                    ctx.strokeStyle = 'rgba(0, 229, 255, 0.85)';
                    ctx.lineWidth = 5;
                    ctx.strokeRect(6, 6, 244, 116);
                    ctx.fillRect(6, 6, 244, 116);

                    ctx.font = '700 48px Chakra Petch, sans-serif';
                    ctx.fillStyle = '#FFFFFF';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(text, 128, 64);

                    const texture = new THREE.CanvasTexture(canvas);
                    const mat = new THREE.SpriteMaterial({ map: texture, depthTest: false });
                    const sprite = new THREE.Sprite(mat);
                    sprite.scale.set(2.4, 1.2, 1);
                    return sprite;
                }

                const binaryStr = atob(modelB64);
                const bytes = new Uint8Array(binaryStr.length);
                for (let i = 0; i < binaryStr.length; i++) {
                    bytes[i] = binaryStr.charCodeAt(i);
                }

                let selectedMeshRef = null;

                const gltfLoader = new THREE.GLTFLoader();
                gltfLoader.parse(bytes.buffer, '', function(gltf) {
                    const model = gltf.scene;
                    scene.add(model);
                    model.updateMatrixWorld(true);
                    loaderText.style.display = 'none';

                    const rawSensors = [];

                    model.traverse(function(child) {
                        if (child.isLine || child.isLineSegments) {
                            child.visible = false;
                            return;
                        }

                        if (child.isMesh) {
                            const name = child.name;
                            const uName = name.toUpperCase();

                            if (uName.includes("BOX001")) {
                                child.visible = false;
                                return;
                            }

                            const isParasiticRing = (
                                uName.includes("RING") ||
                                uName.includes("SEGMENT") ||
                                uName.includes("JOINT") ||
                                uName.includes("SEAM") ||
                                uName.includes("BORDER") ||
                                uName.includes("EDGE") ||
                                uName.includes("FRAME") ||
                                uName.includes("CIRCLE") ||
                                uName.includes("DISC") ||
                                uName.includes("DISK") ||
                                uName.includes("CAP") ||
                                uName.includes("CONTOUR") ||
                                uName.includes("PLUG") ||
                                uName.includes("COVER")
                            );

                            if (isParasiticRing && !uName.startsWith("TA-") && !uName.startsWith("TB-")) {
                                child.visible = false;
                                return;
                            }

                            const isSensorObject = (
                                uName.startsWith("TA-") || 
                                uName.startsWith("TB-") || 
                                uName.includes("-CS") || 
                                uName.includes("-S") || 
                                uName.includes("-TP")
                            );

                            if (isSensorObject) {
                                rawSensors.push(child);
                            } else {
                                const isTunnel = (
                                    uName.includes("TUNNEL") || 
                                    uName.includes("TÜNEL") || 
                                    uName === "TA" || 
                                    uName === "TB" || 
                                    uName.startsWith("TA_") || 
                                    uName.startsWith("TB_")
                                );

                                if (isTunnel) {
                                    tunnelMeshes.push(child);
                                } else {
                                    child.material = new THREE.MeshStandardMaterial({
                                        color: 0x141E2D,
                                        roughness: 0.8
                                    });
                                }
                            }
                        }
                    });

                    // 1. СТРОГИЙ ОТБОР СЕНСОРОВ ПО КАТЕГОРИИ
                    const targetMeshes = [];

                    rawSensors.forEach(child => {
                        child.visible = false;

                        const name = child.name;
                        const uName = name.toUpperCase();
                        const sensorId = extractSensorId(name);

                        let isCategory = false;
                        if (payload.comp === "hoop") {
                            if (uName.includes("-CS")) isCategory = true;
                        } else if (payload.comp === "axial") {
                            if (uName.includes("-S") && !uName.includes("-CS")) isCategory = true;
                        } else if (payload.comp === "temp") {
                            if (uName.includes("-TP")) isCategory = true;
                            else if (checkSensorData(sensorId, "temp").found) isCategory = true;
                        }

                        if (!isCategory) return;

                        const dataInfo = checkSensorData(sensorId, payload.comp);
                        const hasData = dataInfo.found;
                        const sensorName = dataInfo.key;
                        const val = dataInfo.val;

                        const wPos = new THREE.Vector3();
                        child.getWorldPosition(wPos);

                        targetMeshes.push({
                            mesh: child,
                            pos: wPos,
                            sensorName: sensorName,
                            hasData: hasData,
                            val: val
                        });
                    });

                    // 2. ДЕДУПЛИКАЦИЯ ТОЛЬКО ДЛЯ ИДЕНТИЧНЫХ ДАТЧИКОВ
                    const finalSensors = [];
                    targetMeshes.forEach(item => {
                        let duplicate = null;
                        for (let f of finalSensors) {
                            if (f.pos.distanceTo(item.pos) < 0.12 && getCanonicalSensorId(f.sensorName) === getCanonicalSensorId(item.sensorName)) {
                                duplicate = f;
                                break;
                            }
                        }

                        if (!duplicate) {
                            finalSensors.push(item);
                        } else {
                            if (!duplicate.hasData && item.hasData) {
                                duplicate.hasData = true;
                                duplicate.val = item.val;
                                duplicate.sensorName = item.sensorName;
                                duplicate.mesh = item.mesh;
                            }
                        }
                    });

                    // 3. РЕНДЕРИНГ МАРКЕРОВ В НЕЗАВИСИМОМ СЛОЕ
                    finalSensors.forEach(item => {
                        const hasData = item.hasData;
                        const sensorName = item.sensorName;
                        const val = item.val;

                        if (hasData || payload.showNoDataRed) {
                            const isSelected = (sensorName === payload.selectedSensor || getCanonicalSensorId(sensorName) === getCanonicalSensorId(payload.selectedSensor || ""));

                            let sensorColor = 0xFFFFFF; // Белый по умолчанию
                            if (isSelected) {
                                sensorColor = 0xFFD700; // Золотой
                            } else if (!hasData) {
                                sensorColor = 0xFF0033; // Красный
                            }

                            const sensorMat = new THREE.MeshBasicMaterial({
                                color: sensorColor,
                                side: THREE.DoubleSide,
                                transparent: false,
                                opacity: 1.0,
                                depthTest: true,
                                depthWrite: true
                            });

                            const wQuat = new THREE.Quaternion();
                            const wScale = new THREE.Vector3();
                            item.mesh.getWorldQuaternion(wQuat);
                            item.mesh.getWorldScale(wScale);

                            const detachedMesh = new THREE.Mesh(item.mesh.geometry.clone(), sensorMat);
                            detachedMesh.position.copy(item.pos);
                            detachedMesh.quaternion.copy(wQuat);
                            detachedMesh.scale.copy(wScale);

                            detachedMesh.userData.sensorName = sensorName;
                            detachedMesh.userData.val = hasData ? val : NaN;
                            detachedMesh.userData.isUsable = hasData;
                            detachedMesh.userData.isNoData = !hasData;

                            sensorScene.add(detachedMesh);
                            interactiveSensors.push(detachedMesh);

                            if (isSelected) {
                                selectedMeshRef = detachedMesh;
                                updateHud(sensorName, val);
                            }
                        }
                    });

                    // РАСЧЕТ РЕАЛЬНОГО ДИАПАЗОНА
                    const validVals = interactiveSensors
                        .filter(s => s.userData.isUsable && !isNaN(s.userData.val))
                        .map(s => s.userData.val);

                    let dynamicClim = [0.0, 1.0];
                    if (validVals.length > 0) {
                        let dMin = Math.min(...validVals);
                        let dMax = Math.max(...validVals);
                        if (Math.abs(dMax - dMin) < 0.001) {
                            dMin -= 1.0;
                            dMax += 1.0;
                        }
                        dynamicClim = [dMin, dMax];
                    } else if (payload.clim) {
                        dynamicClim = payload.clim;
                    }

                    const finalMin = dynamicClim[0];
                    const finalMax = dynamicClim[1];
                    const finalMid = (finalMin + finalMax) / 2.0;

                    lblMax.innerText = (finalMax > 0 ? "+" : "") + finalMax.toFixed(1);
                    lblMid.innerText = (finalMid > 0 ? "+" : "") + finalMid.toFixed(1);
                    lblMin.innerText = (finalMin > 0 ? "+" : "") + finalMin.toFixed(1);

                    const interpolationSensors = [];
                    interactiveSensors.forEach(sMesh => {
                        if (sMesh.userData.isUsable && !sMesh.userData.isNoData) {
                            const uName = sMesh.userData.sensorName.toUpperCase();
                            const tun = uName.startsWith("TB") ? "TB" : (uName.startsWith("TA") ? "TA" : "ALL");

                            interpolationSensors.push({
                                pos: sMesh.position.clone(),
                                val: sMesh.userData.val,
                                tun: tun,
                                name: sMesh.userData.sensorName
                            });
                        }
                    });

                    // ИНТЕРПОЛЯЦИЯ СВОДА ТОННЕЛЯ
                    const R_INFLUENCE = 48.0;

                    tunnelMeshes.forEach(tMesh => {
                        const geom = tMesh.geometry;
                        if (!geom || !geom.attributes || !geom.attributes.position) return;

                        const posAttr = geom.attributes.position;
                        const colors = new Float32Array(posAttr.count * 3);
                        const localV = new THREE.Vector3();
                        const worldV = new THREE.Vector3();

                        const uName = tMesh.name.toUpperCase();
                        const isTB = uName.includes("TB");
                        const activeTun = isTB ? "TB" : "TA";
                        
                        let pool = interpolationSensors.filter(s => s.tun === activeTun || s.tun === "ALL");
                        if (pool.length < 2) pool = interpolationSensors;

                        tMesh.updateMatrixWorld(true);

                        if (pool.length === 0) {
                            for (let i = 0; i < posAttr.count; i++) {
                                const idx = i * 3;
                                colors[idx] = 0.082;
                                colors[idx + 1] = 0.110;
                                colors[idx + 2] = 0.157;
                            }
                        } else {
                            for (let i = 0; i < posAttr.count; i++) {
                                localV.fromBufferAttribute(posAttr, i);
                                worldV.copy(localV).applyMatrix4(tMesh.matrixWorld);

                                let totalWeight = 0;
                                let accumR = 0, accumG = 0, accumB = 0;

                                for (let j = 0; j < pool.length; j++) {
                                    const s = pool[j];
                                    const d = worldV.distanceTo(s.pos);
                                    
                                    if (d < R_INFLUENCE) {
                                        const rNorm = d / R_INFLUENCE;
                                        const wEnvelope = Math.pow(1.0 - Math.pow(rNorm, 1.3), 1.2);
                                        const w = wEnvelope / (Math.pow(d, 1.8) + 0.15);

                                        const c = getColorForValue(s.val, dynamicClim);
                                        accumR += c.r * w;
                                        accumG += c.g * w;
                                        accumB += c.b * w;
                                        totalWeight += w;
                                    }
                                }

                                const idx = i * 3;
                                if (totalWeight > 0.000001) {
                                    colors[idx] = accumR / totalWeight;
                                    colors[idx + 1] = accumG / totalWeight;
                                    colors[idx + 2] = accumB / totalWeight;
                                } else {
                                    colors[idx] = 0.082;
                                    colors[idx + 1] = 0.110;
                                    colors[idx + 2] = 0.157;
                                }
                            }
                        }

                        geom.setAttribute('color', new THREE.BufferAttribute(colors, 3));
                        geom.attributes.color.needsUpdate = true;
                        
                        const isTransparent = payload.tunnelOpacity < 0.98;
                        tMesh.material = new THREE.MeshStandardMaterial({
                            color: 0xffffff,
                            vertexColors: true,
                            transparent: isTransparent,
                            opacity: payload.tunnelOpacity,
                            roughness: 0.18,
                            metalness: 0.02,
                            depthWrite: !isTransparent,
                            side: THREE.DoubleSide
                        });
                        tMesh.renderOrder = 0;
                        tMesh.material.needsUpdate = true;
                    });

                    const boxTA = new THREE.Box3();
                    const boxTB = new THREE.Box3();
                    let hasTA = false, hasTB = false;

                    tunnelMeshes.forEach(tm => {
                        const u = tm.name.toUpperCase();
                        if (u.includes("TB")) {
                            boxTB.expandByObject(tm);
                            hasTB = true;
                        } else if (u.includes("TA")) {
                            boxTA.expandByObject(tm);
                            hasTA = true;
                        }
                    });

                    const portalsGroup = new THREE.Group();

                    if (hasTA) {
                        const cA = boxTA.getCenter(new THREE.Vector3());
                        const spriteTA = createPortalMarker("TA");
                        spriteTA.position.set(cA.x, boxTA.max.y + 3.2, boxTA.min.z - 2.0);
                        portalsGroup.add(spriteTA);
                    }

                    if (hasTB) {
                        const cB = boxTB.getCenter(new THREE.Vector3());
                        const spriteTB = createPortalMarker("TB");
                        spriteTB.position.set(cB.x, boxTB.max.y + 3.2, boxTB.min.z - 2.0);
                        portalsGroup.add(spriteTB);
                    }

                    scene.add(portalsGroup);

                    if (payload.showMeters) {
                        const overallBox = new THREE.Box3();
                        tunnelMeshes.forEach(tm => overallBox.expandByObject(tm));

                        if (!overallBox.isEmpty()) {
                            const size = overallBox.getSize(new THREE.Vector3());
                            const rulerGroup = new THREE.Group();

                            const isZAxis = size.z >= size.x;
                            const lengthM = isZAxis ? size.z : size.x;
                            const startCoord = isZAxis ? overallBox.min.z : overallBox.min.x;
                            const endCoord = isZAxis ? overallBox.max.z : overallBox.max.x;

                            const step = 10.0;
                            const stepsCount = Math.floor(lengthM / step);
                            const totalDistanceM = stepsCount * step;

                            const yRuler = overallBox.min.y - 0.2;
                            const lateralPos = isZAxis ? (overallBox.max.x + 3.5) : (overallBox.max.z + 3.5);

                            const linePoints = [];
                            if (isZAxis) {
                                linePoints.push(new THREE.Vector3(lateralPos, yRuler, startCoord));
                                linePoints.push(new THREE.Vector3(lateralPos, yRuler, endCoord));
                            } else {
                                linePoints.push(new THREE.Vector3(startCoord, yRuler, lateralPos));
                                linePoints.push(new THREE.Vector3(endCoord, yRuler, lateralPos));
                            }

                            const axisGeom = new THREE.BufferGeometry().setFromPoints(linePoints);
                            const axisMat = new THREE.LineBasicMaterial({ color: 0x00E5FF, linewidth: 3 });
                            rulerGroup.add(new THREE.Line(axisGeom, axisMat));

                            for (let i = 0; i <= stepsCount; i++) {
                                const currentPos = startCoord + i * step;
                                const reversedDistance = (totalDistanceM - (i * step)).toFixed(0);
                                const distanceText = reversedDistance + " m";

                                const tickPoints = [];
                                if (isZAxis) {
                                    tickPoints.push(new THREE.Vector3(lateralPos - 0.8, yRuler, currentPos));
                                    tickPoints.push(new THREE.Vector3(lateralPos + 0.8, yRuler, currentPos));
                                } else {
                                    tickPoints.push(new THREE.Vector3(currentPos, yRuler, lateralPos - 0.8));
                                    tickPoints.push(new THREE.Vector3(currentPos, yRuler, lateralPos + 0.8));
                                }

                                const tickGeom = new THREE.BufferGeometry().setFromPoints(tickPoints);
                                rulerGroup.add(new THREE.Line(tickGeom, axisMat));

                                const label = createRulerLabel(distanceText);
                                if (isZAxis) {
                                    label.position.set(lateralPos + 2.4, yRuler + 0.4, currentPos);
                                } else {
                                    label.position.set(currentPos, yRuler + 0.4, lateralPos + 2.4);
                                }
                                rulerGroup.add(label);
                            }

                            scene.add(rulerGroup);
                        }
                    }

                    // ПОЗИЦИОНИРОВАНИЕ КАМЕРЫ (КРУПНЫЙ ПЛАН)
                    const lastSelected = sessionStorage.getItem('threejs_last_selected');
                    const isNewSensorSelected = (payload.selectedSensor && payload.selectedSensor !== "Seçiniz..." && payload.selectedSensor !== lastSelected);

                    if (selectedMeshRef && isNewSensorSelected) {
                        sessionStorage.setItem('threejs_last_selected', payload.selectedSensor);
                        flyCameraTo(selectedMeshRef, true);
                    } else {
                        const savedStateStr = sessionStorage.getItem('threejs_camera_state');
                        if (savedStateStr) {
                            try {
                                const st = JSON.parse(savedStateStr);
                                camera.position.set(st.pos[0], st.pos[1], st.pos[2]);
                                controls.target.set(st.target[0], st.target[1], st.target[2]);
                                controls.update();
                            } catch(e) {}
                        } else {
                            const tunnelBox = new THREE.Box3();
                            if (tunnelMeshes.length > 0) {
                                tunnelMeshes.forEach(tm => tunnelBox.expandByObject(tm));
                            } else {
                                tunnelBox.setFromObject(model);
                            }

                            const center = tunnelBox.getCenter(new THREE.Vector3());
                            const size = tunnelBox.getSize(new THREE.Vector3());
                            const maxDim = Math.max(size.x, size.y, size.z, 20.0);

                            controls.target.copy(center);
                            camera.position.set(
                                center.x - maxDim * 0.40,
                                center.y + maxDim * 0.45,
                                center.z + maxDim * 0.55
                            );
                            controls.update();
                        }
                    }

                }, undefined, function(err) {
                    loaderText.innerHTML = "Model yüklenirken hata oluştu!";
                    console.error(err);
                });

                function updateHud(name, val) {
                    if (val !== undefined && !isNaN(val)) {
                        selectedHud.style.display = 'block';
                        hudName.innerText = name;
                        const valTxt = (val > 0 ? "+" + val.toFixed(2) : val.toFixed(2)) + " " + payload.unit;
                        hudVal.innerText = valTxt;
                    }
                }

                function flyCameraTo(targetMesh, animate = true) {
                    const targetPos = targetMesh.position.clone();

                    const offsetDir = new THREE.Vector3(targetPos.x, 0, targetPos.z).normalize();
                    if (offsetDir.length() === 0) offsetDir.set(1, 0, 0);

                    const endCamPos = targetPos.clone().add(offsetDir.multiplyScalar(4.0)).add(new THREE.Vector3(0, 1.8, 0));

                    if (!animate) {
                        camera.position.copy(endCamPos);
                        controls.target.copy(targetPos);
                        controls.update();
                        return;
                    }

                    new TWEEN.Tween(controls.target)
                        .to(targetPos, 1400)
                        .easing(TWEEN.Easing.Cubic.InOut)
                        .start();

                    new TWEEN.Tween(camera.position)
                        .to(endCamPos, 1400)
                        .easing(TWEEN.Easing.Cubic.InOut)
                        .onUpdate(() => controls.update())
                        .onComplete(() => {
                            const camState = {
                                pos: [camera.position.x, camera.position.y, camera.position.z],
                                target: [controls.target.x, controls.target.y, controls.target.z]
                            };
                            sessionStorage.setItem('threejs_camera_state', JSON.stringify(camState));
                        })
                        .start();
                }

                function getIntersectedSensor(e) {
                    const rect = renderer.domElement.getBoundingClientRect();
                    mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
                    mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

                    raycaster.setFromCamera(mouse, camera);
                    const intersects = raycaster.intersectObjects(interactiveSensors, true);

                    if (intersects.length > 0) {
                        let obj = intersects[0].object;
                        while (obj && !obj.userData.sensorName && obj.parent) {
                            obj = obj.parent;
                        }
                        return (obj && (obj.userData.isUsable || obj.userData.isNoData)) ? obj : null;
                    }
                    return null;
                }

                window.addEventListener('click', function(e) {
                    const sensorMesh = getIntersectedSensor(e);
                    if (sensorMesh) {
                        const sensorName = sensorMesh.userData.sensorName;
                        const sensorVal = sensorMesh.userData.val;
                        
                        interactiveSensors.forEach(m => {
                            if (m.userData.isUsable) {
                                const isSel = (m.userData.sensorName === sensorName || getCanonicalSensorId(m.userData.sensorName) === getCanonicalSensorId(sensorName));
                                m.material.color.setHex(isSel ? 0xFFD700 : 0xFFFFFF);
                            }
                        });

                        flyCameraTo(sensorMesh, true);
                        updateHud(sensorName, sensorVal);
                    }
                });

                window.addEventListener('mousemove', function(e) {
                    const sensorMesh = getIntersectedSensor(e);
                    if (sensorMesh) {
                        const name = sensorMesh.userData.sensorName;
                        const val = sensorMesh.userData.val;
                        const isUsable = sensorMesh.userData.isUsable;
                        const isNoData = sensorMesh.userData.isNoData;

                        tooltip.style.display = 'block';
                        tooltip.style.left = (e.clientX + 14) + 'px';
                        tooltip.style.top = (e.clientY + 14) + 'px';
                        
                        if (isUsable) {
                            const valTxt = (val > 0 ? "+" + val : val) + " " + payload.unit;
                            tooltip.innerHTML = '<b>' + name + '</b><br><span style="color:#00E5FF;">Değer: ' + valTxt + '</span><br><span style="color:#8397AD; font-size:11px;">(Seçmek için tıkla)</span>';
                            renderer.domElement.style.cursor = 'pointer';
                        } else if (isNoData) {
                            tooltip.innerHTML = '<b>' + name + '</b><br><span style="color:#FF0033; font-weight:700;">Durum: Veri Yok / Belirsiz</span>';
                            renderer.domElement.style.cursor = 'pointer';
                        }
                    } else {
                        tooltip.style.display = 'none';
                        renderer.domElement.style.cursor = 'default';
                    }
                });

                window.addEventListener('resize', function() {
                    camera.aspect = container.clientWidth / container.clientHeight;
                    camera.updateProjectionMatrix();
                    renderer.setSize(container.clientWidth, container.clientHeight);
                });

                // ДВУХПРОХОДНЫЙ РЕНДЕР
                function animate(time) {
                    requestAnimationFrame(animate);
                    TWEEN.update(time);
                    controls.update();

                    renderer.clear();
                    renderer.render(scene, camera);

                    renderer.clearDepth();
                    renderer.render(sensorScene, camera);
                }
                requestAnimationFrame(animate);
            </script>
        </body>
        </html>
        """

        st.components.v1.html(threejs_html, height=760, scrolling=False)
