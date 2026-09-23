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

st.set_page_config(page_title="LOGGIS 3B - THY", layout="wide")

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

logo_b64 = ""
if os.path.exists(LOGO_PATH):
    with open(LOGO_PATH, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()

logo_tag = f'<img src="data:image/jpeg;base64,{logo_b64}" style="width: 200px; height: auto; display: block; opacity: 0.85; border-radius: 4px;" alt="DESTECH">' if logo_b64 else '<span class="destech-badge">DESTECH</span>'

st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-top: -20px; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid rgba(0, 200, 230, 0.15);">
    <div style="display: flex; flex-direction: column; justify-content: center;">
        <h1 style="margin: 0 !important; padding: 0 !important; font-size: 32px !important; line-height: 1.1 !important;">LOGGIS 3B - THY</h1>
        <div style="color: #00C8E6; font-weight: 700; font-size: 13px; letter-spacing: 1.5px; margin-top: 3px;">SENSÖR VE TÜNEL İNTERPOLASYON SİSTEMİ (3DS MAX)</div>
    </div>
    <div style="display: flex; align-items: center;">
        {logo_tag}
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

# --- ИНТЕРФЕЙС STREAMLIT ---
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
v_map = cur_layer["values"]
vals = [v for v in v_map.values() if not np.isnan(v)]

if not vals:
    clim = [0.0, 1.0]
elif selected_comp == "temp":
    clim = [round(float(min(vals)), 1), round(float(max(vals)), 1)]
else:
    m = round(max(abs(min(vals)), abs(max(vals)), 1.0), 1)
    clim = [-m, m]

with col_nav:
    st.markdown("---")
    st.subheader("TÜNEL KONTROLLERİ")
    show_ta = st.checkbox("Tünel TA Göster", value=True)
    show_tb = st.checkbox("Tünel TB Göster", value=True)
    tunnel_opacity = st.slider("Tünel Opaklığı (%):", min_value=20, max_value=100, value=90, step=5) / 100.0

    st.markdown("---")
    st.write("**En Son Veri Zamanı:**")
    st.markdown(f"<span class='neon-data' style='font-size: 16px;'>{cur_layer['date'] if cur_layer['date'] else 'Bilinmiyor'}</span>", unsafe_allow_html=True)
    
    st.write("**Aktif Sensör Sayısı:**")
    st.markdown(f"<span class='neon-data' style='font-size: 20px;'>{len(v_map)}</span>", unsafe_allow_html=True)
    
    st.write("**Skala Limitleri:**")
    st.markdown(f"<span class='neon-data' style='font-size: 15px;'>Min: {clim[0]} | Maks: {clim[1]} {cat_cfg['unit']}</span>", unsafe_allow_html=True)

    st.markdown("---")
    selected_sensor = st.selectbox("Sensör Değerini İncele:", options=["Seçiniz..."] + sorted(list(v_map.keys())))
    if selected_sensor != "Seçiniz...":
        st.metric(label=selected_sensor, value=f"{v_map[selected_sensor]:+.2f} {cat_cfg['unit']}")

# --- 3B THREE.JS ОБЛАСТЬ ---
with col_3d:
    model_b64 = get_model_b64(MODEL_PATH)
    
    if not model_b64:
        st.error(f"⚠️ `{MODEL_PATH}` bulunamadı! Lütfen 3ds Max'ten aldığınız .glb modelini `app.py` ile aynı klasöre yükleyiniz.")
    else:
        payload_data = {
            "sensorValues": v_map,
            "selectedSensor": selected_sensor,
            "unit": cat_cfg["unit"],
            "clim": clim,
            "comp": selected_comp,
            "activeTag": cat_cfg["tag"],
            "showTA": show_ta,
            "showTB": show_tb,
            "tunnelOpacity": float(tunnel_opacity)
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
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-size: 13px;
                    pointer-events: none;
                    z-index: 100;
                    box-shadow: 0 4px 14px rgba(0, 200, 230, 0.3);
                }}
                #loader {{
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    color: #00C8E6;
                    font-size: 17px;
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
                    background: rgba(10, 14, 23, 0.85);
                    padding: 12px 14px;
                    border: 1px solid rgba(0, 200, 230, 0.3);
                    border-radius: 6px;
                    z-index: 90;
                    user-select: none;
                }}
                #legend-title {{
                    color: #FFFFFF;
                    font-size: 12px;
                    font-weight: 700;
                    margin-bottom: 8px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                .legend-bar-container {{
                    display: flex;
                    align-items: stretch;
                    height: 220px;
                }}
                #legend-bar {{
                    width: 16px;
                    border-radius: 3px;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    margin-right: 8px;
                }}
                .legend-labels {{
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                    color: #D2DEEC;
                    font-size: 11px;
                    font-weight: 600;
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
                
                <div id="color-legend">
                    <div id="legend-title">[{cat_cfg['unit']}]</div>
                    <div class="legend-bar-container">
                        <div id="legend-bar"></div>
                        <div class="legend-labels">
                            <span>{clim[1]:+.1f}</span>
                            <span>{round((clim[0] + clim[1]) / 2.0, 1):+.1f}</span>
                            <span>{clim[0]:+.1f}</span>
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

                if (payload.comp === "temp") {{
                    legendBar.style.background = "linear-gradient(to bottom, #FF0000, #FF5500, #FFAA00, #FFFF00, #00FF88, #0099FF, #0011DD)";
                }} else if (payload.comp === "axial") {{
                    legendBar.style.background = "linear-gradient(to bottom, #9900CC, #FF00EE, #FFFFFF, #00FF44, #008811)";
                }} else {{
                    legendBar.style.background = "linear-gradient(to bottom, #EE0000, #FF3311, #FFFFFF, #00AAFF, #0033CC)";
                }}

                const scene = new THREE.Scene();
                scene.background = new THREE.Color(0x0A0E17);

                const rootGroup = new THREE.Group();
                scene.add(rootGroup);

                const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.05, 5000);

                const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true, powerPreference: "high-performance" }});
                renderer.setSize(container.clientWidth, container.clientHeight);
                renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
                renderer.toneMapping = THREE.ACESFilmicToneMapping;
                renderer.toneMappingExposure = 1.35;
                container.appendChild(renderer.domElement);

                const controls = new THREE.OrbitControls(camera, renderer.domElement);
                controls.enableDamping = true;
                controls.dampingFactor = 0.06;
                controls.minDistance = 0.5;
                controls.maxDistance = 2500;
                controls.zoomSpeed = 1.15;
                controls.panSpeed = 1.0;
                controls.screenSpacePanning = true;

                const ambientLight = new THREE.AmbientLight(0xffffff, 1.4);
                scene.add(ambientLight);

                const dirLight1 = new THREE.DirectionalLight(0x00C8E6, 1.5);
                dirLight1.position.set(50, 70, 60);
                scene.add(dirLight1);

                const dirLight2 = new THREE.DirectionalLight(0xffffff, 1.0);
                dirLight2.position.set(-50, -30, -60);
                scene.add(dirLight2);

                const sensorMeshes = [];
                const tunnelMeshes = [];
                const raycaster = new THREE.Raycaster();
                const mouse = new THREE.Vector2();

                function getColorForValue(val, clim, comp) {{
                    if (val === undefined || isNaN(val)) return new THREE.Color(0x333333);
                    const min = clim[0], max = clim[1];
                    let t = (val - min) / ((max - min) || 1.0);
                    t = Math.max(0, Math.min(1, t));

                    const c = new THREE.Color();
                    if (comp === "temp") {{
                        c.setHSL((1.0 - t) * 0.68, 1.0, 0.5);
                    }} else if (comp === "axial") {{
                        if (t < 0.5) {{
                            const f = t * 2.0;
                            c.setRGB(1.0 - f, 1.0, 1.0 - f * 0.7);
                        }} else {{
                            const f = (t - 0.5) * 2.0;
                            c.setRGB(0.7 + f * 0.3, 1.0 - f * 0.9, 0.9 + f * 0.1);
                        }}
                    }} else {{
                        if (t < 0.5) {{
                            const f = t * 2.0;
                            c.setRGB(f, f * 0.85 + 0.1, 1.0);
                        }} else {{
                            const f = (t - 0.5) * 2.0;
                            c.setRGB(1.0, 1.0 - f * 0.9, 1.0 - f);
                        }}
                    }}
                    return c;
                }}

                function isSensorForActiveCategory(name, activeTag) {{
                    if (activeTag === "-CS") return name.includes("-CS");
                    if (activeTag === "-S") return name.includes("-S") && !name.includes("-CS");
                    if (activeTag === "-TP") return name.includes("-TP");
                    return false;
                }}

                const binaryStr = atob(modelB64);
                const bytes = new Uint8Array(binaryStr.length);
                for (let i = 0; i < binaryStr.length; i++) {{
                    bytes[i] = binaryStr.charCodeAt(i);
                }}

                let selectedMeshRef = null;

                const gltfLoader = new THREE.GLTFLoader();
                gltfLoader.parse(bytes.buffer, '', function(gltf) {{
                    const model = gltf.scene;
                    rootGroup.add(model);
                    model.updateMatrixWorld(true);
                    loaderText.style.display = 'none';

                    // 1. ПОИСК ОБЪЕКТОВ
                    model.traverse(function(child) {{
                        if (child.isMesh) {{
                            const name = child.name;
                            const uName = name.toUpperCase();

                            // Каркасный Box001
                            if (uName.includes("BOX001")) {{
                                child.material = new THREE.MeshBasicMaterial({{
                                    color: 0x1E3A5F,
                                    wireframe: true,
                                    transparent: true,
                                    opacity: 0.15
                                }});
                                return;
                            }}

                            const isSensor = (
                                uName.includes("-CS") || 
                                uName.includes("-S") || 
                                uName.includes("-TP") || 
                                payload.sensorValues.hasOwnProperty(name)
                            );

                            if (isSensor) {{
                                sensorMeshes.push(child);
                                child.userData.sensorName = name;
                                child.userData.isSensor = true;

                                const isCategoryMatch = isSensorForActiveCategory(name, payload.activeTag);
                                const val = payload.sensorValues[name];
                                child.userData.val = val;
                                child.userData.isActiveCategory = isCategoryMatch;

                                const isSelected = (name === payload.selectedSensor);

                                if (isCategoryMatch && val !== undefined && !isNaN(val)) {{
                                    const sensorColor = isSelected ? new THREE.Color(0xFFD700) : getColorForValue(val, payload.clim, payload.comp);

                                    child.material = new THREE.MeshStandardMaterial({{
                                        color: sensorColor,
                                        emissive: isSelected ? new THREE.Color(0xFFD700) : sensorColor,
                                        emissiveIntensity: isSelected ? 1.0 : 0.75,
                                        roughness: 0.15,
                                        metalness: 0.2
                                    }});

                                    if (isSelected) {{
                                        child.scale.set(1.75, 1.75, 1.75);
                                        selectedMeshRef = child;
                                    }}
                                }} else {{
                                    child.material = new THREE.MeshStandardMaterial({{
                                        color: 0x222C38,
                                        transparent: true,
                                        opacity: 0.25,
                                        roughness: 0.9,
                                        metalness: 0.0
                                    }});
                                    child.scale.set(0.9, 0.9, 0.9);
                                }}
                            }} else {{
                                // Тела тоннелей
                                const isTunnelMesh = (
                                    uName.includes("TA") || 
                                    uName.includes("TB") || 
                                    uName.includes("TUNNEL") || 
                                    uName.includes("TÜNEL") || 
                                    uName.includes("CYLINDER")
                                );

                                if (isTunnelMesh) {{
                                    tunnelMeshes.push(child);
                                }} else {{
                                    child.material = new THREE.MeshStandardMaterial({{
                                        color: 0x141E2D,
                                        roughness: 0.8,
                                        metalness: 0.1
                                    }});
                                }}
                            }}
                        }}
                    }});

                    // 2. СБОР МИРОВЫХ КООРДИНАТ ДАТЧИКОВ
                    const activeSensors = [];
                    sensorMeshes.forEach(sMesh => {{
                        if (sMesh.userData.isActiveCategory && sMesh.userData.val !== undefined && !isNaN(sMesh.userData.val)) {{
                            const wPos = new THREE.Vector3();
                            sMesh.getWorldPosition(wPos);
                            const uName = sMesh.userData.sensorName.toUpperCase();
                            const tun = uName.startsWith("TB") ? "TB" : (uName.startsWith("TA") ? "TA" : "ALL");

                            activeSensors.push({{
                                pos: wPos,
                                val: sMesh.userData.val,
                                tun: tun,
                                name: sMesh.userData.sensorName
                            }});
                        }}
                    }});

                    // 3. ПРЯМАЯ ИНТЕРПОЛЯЦИЯ НА ВЕРШИНЫ ВАШЕЙ МОДЕЛИ 3DS MAX
                    tunnelMeshes.forEach(tMesh => {{
                        const uName = tMesh.name.toUpperCase();
                        const isTB = uName.includes("TB");
                        
                        if (isTB && !payload.showTB) {{
                            tMesh.visible = false;
                            return;
                        }}
                        if (!isTB && !payload.showTA) {{
                            tMesh.visible = false;
                            return;
                        }}
                        tMesh.visible = true;

                        const geom = tMesh.geometry;
                        if (!geom || !geom.attributes || !geom.attributes.position) return;

                        const posAttr = geom.attributes.position;
                        const colors = new Float32Array(posAttr.count * 3);
                        const localV = new THREE.Vector3();
                        const worldV = new THREE.Vector3();

                        const activeTun = isTB ? "TB" : "TA";
                        let pool = activeSensors.filter(s => s.tun === activeTun || s.tun === "ALL");
                        if (pool.length < 3) pool = activeSensors;

                        tMesh.updateMatrixWorld(true);

                        for (let i = 0; i < posAttr.count; i++) {{
                            localV.fromBufferAttribute(posAttr, i);
                            // Координата вершины в мировом пространстве сцены
                            worldV.copy(localV).applyMatrix4(tMesh.matrixWorld);

                            let totalWeight = 0;
                            let accumR = 0, accumG = 0, accumB = 0;

                            for (let j = 0; j < pool.length; j++) {{
                                const s = pool[j];
                                const d = worldV.distanceTo(s.pos);
                                
                                // Мягкий спад веса, чтобы весь тоннель был окрашен
                                const w = 1.0 / Math.pow(d + 0.6, 2.0);
                                const c = getColorForValue(s.val, payload.clim, payload.comp);

                                accumR += c.r * w;
                                accumG += c.g * w;
                                accumB += c.b * w;
                                totalWeight += w;
                            }}

                            const idx = i * 3;
                            if (totalWeight > 0) {{
                                colors[idx] = accumR / totalWeight;
                                colors[idx + 1] = accumG / totalWeight;
                                colors[idx + 2] = accumB / totalWeight;
                            }} else {{
                                colors[idx] = 0.12;
                                colors[idx + 1] = 0.18;
                                colors[idx + 2] = 0.28;
                            }}
                        }}

                        geom.setAttribute('color', new THREE.BufferAttribute(colors, 3));
                        geom.attributes.color.needsUpdate = true;
                        
                        const isTransparent = payload.tunnelOpacity < 0.98;
                        tMesh.material = new THREE.MeshStandardMaterial({{
                            color: 0xffffff, // Белый базовый цвет для чистого отображения градиента
                            vertexColors: true,
                            transparent: isTransparent,
                            opacity: payload.tunnelOpacity,
                            roughness: 0.35,
                            metalness: 0.05,
                            depthWrite: !isTransparent,
                            side: THREE.DoubleSide
                        }});
                        tMesh.material.needsUpdate = true;
                    }});

                    // 4. НАСТОЯЩЕЕ ЦЕНТРИРОВАНИЕ МОДЕЛИ ТОННЕЛЕЙ В (0,0,0)
                    // Вычисляем бокс только по реальным тоннелям (игнорируя улетевшие вспомогательные боксы)
                    const tunnelBox = new THREE.Box3();
                    if (tunnelMeshes.length > 0) {{
                        tunnelMeshes.forEach(tm => tunnelBox.expandByObject(tm));
                    }} else {{
                        tunnelBox.setFromObject(model);
                    }}

                    const centerOffset = tunnelBox.getCenter(new THREE.Vector3());

                    // Перемещаем всю корневую группу так, чтобы тоннели сели ровно в (0,0,0)
                    rootGroup.position.sub(centerOffset);
                    rootGroup.updateMatrixWorld(true);

                    // Пересчитываем габариты после центрирования
                    const finalBox = new THREE.Box3().setFromObject(rootGroup);
                    const size = finalBox.getSize(new THREE.Vector3());

                    // Устанавливаем сетку точно под днище тоннелей
                    const grid = new THREE.GridHelper(Math.max(size.x, size.z) * 1.5, 50, 0x00C8E6, 0x141E30);
                    grid.position.y = finalBox.min.y - 0.2;
                    scene.add(grid);

                    // 5. ПОЗИЦИОНИРОВАНИЕ КАМЕРЫ СТРОГО ПО ЦЕНТРУ
                    controls.target.set(0, 0, 0);

                    if (selectedMeshRef) {{
                        flyCameraTo(selectedMeshRef, false);
                    }} else {{
                        const maxDim = Math.max(size.x, size.y, size.z, 20.0);
                        const fovRad = (camera.fov * Math.PI) / 180.0;
                        let idealDist = (maxDim / 2.0) / Math.tan(fovRad / 2.0) * 1.1;

                        camera.position.set(
                            size.x * 0.7 + 12.0,
                            size.y * 0.6 + 8.0,
                            idealDist * 0.75
                        );
                        controls.update();
                    }}

                }}, undefined, function(err) {{
                    loaderText.innerHTML = "Model yüklenirken hata oluştu!";
                    console.error(err);
                }});

                function flyCameraTo(targetMesh, animate = true) {{
                    const targetPos = new THREE.Vector3();
                    targetMesh.getWorldPosition(targetPos);

                    const offsetDir = new THREE.Vector3(targetPos.x, 0, targetPos.z).normalize();
                    if (offsetDir.length() === 0) offsetDir.set(1, 0, 0);

                    const endCamPos = targetPos.clone().add(offsetDir.multiplyScalar(2.2)).add(new THREE.Vector3(0, 0.8, 0));

                    if (!animate) {{
                        camera.position.copy(endCamPos);
                        controls.target.copy(targetPos);
                        controls.update();
                        return;
                    }}

                    new TWEEN.Tween(controls.target)
                        .to(targetPos, 1000)
                        .easing(TWEEN.Easing.Cubic.InOut)
                        .start();

                    new TWEEN.Tween(camera.position)
                        .to(endCamPos, 1000)
                        .easing(TWEEN.Easing.Cubic.InOut)
                        .start();
                }}

                window.addEventListener('mousemove', function(e) {{
                    const rect = renderer.domElement.getBoundingClientRect();
                    mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
                    mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

                    raycaster.setFromCamera(mouse, camera);
                    const intersects = raycaster.intersectObjects(sensorMeshes);

                    if (intersects.length > 0) {{
                        const mesh = intersects[0].object;
                        const name = mesh.userData.sensorName;
                        const val = mesh.userData.val;
                        const isMatch = mesh.userData.isActiveCategory;
                        const valTxt = (val !== undefined && !isNaN(val)) ? (val > 0 ? "+" + val : val) + " " + payload.unit : "Bilinmiyor";

                        tooltip.style.display = 'block';
                        tooltip.style.left = (e.clientX + 14) + 'px';
                        tooltip.style.top = (e.clientY + 14) + 'px';
                        
                        if (isMatch) {{
                            tooltip.innerHTML = '<b>' + name + '</b><br><span style="color:#00C8E6;">Aktif Analiz Değeri: ' + valTxt + '</span>';
                        }} else {{
                            tooltip.innerHTML = '<b>' + name + '</b><br><span style="color:#8899AA;">(Başka analiz kategorisi)</span>';
                        }}
                        renderer.domElement.style.cursor = 'pointer';
                    }} else {{
                        tooltip.style.display = 'none';
                        renderer.domElement.style.cursor = 'default';
                    }}
                }});

                window.addEventListener('resize', function() {{
                    camera.aspect = container.clientWidth / container.clientHeight;
                    camera.updateProjectionMatrix();
                    renderer.setSize(container.clientWidth, container.clientHeight);
                }});

                function animate(time) {{
                    requestAnimationFrame(animate);
                    TWEEN.update(time);
                    controls.update();
                    renderer.render(scene, camera);
                }}
                requestAnimationFrame(animate);
            </script>
        </body>
        </html>
        """

        st.components.v1.html(threejs_html, height=740, scrolling=False)
