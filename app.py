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
                        if (cells.length > 1 && (cells[0].includes('/') || cells[0].includes(':) || cells[0].includes('-'))) {
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
        st.error(f"⚠️ `{MODEL_PATH}` bulunamadı! Lütfen 3ds Max'ten aldığınız .glb modelini `app.py` ile aynı klasöre yükлейiniz.")
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

        # HTML/JS Шаблон с безопасной маской прозрачности вместо удаления полигонов
        threejs_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ margin: 0; padding: 0; overflow: hidden; background-color: #0A0E17; font-family: 'Chakra Petch', sans-serif; }}
                #canvas-container {{ width: 100vw; height: 100vh; position: relative; }}
                #sensor-tooltip {{ position: absolute; display: none; background: rgba(14, 24, 42, 0.95); border: 1px solid #00C8E6; color: #FFFFFF; padding: 8px 14px; border-radius: 6px; font-size: 14px; pointer-events: none; z-index: 100; box-shadow: 0 6px 18px rgba(0, 200, 230, 0.35); }}
                #loader {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: #00C8E6; font-size: 18px; font-weight: 700; letter-spacing: 1px; z-index: 10; }}
            </style>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
        </head>
        <body>
            <div id="canvas-container">
                <div id="loader">3B MODEL VE VERİLER YÜKLENİYOR...</div>
                <div id="sensor-tooltip"></div>
            </div>

            <script>
                const payload = {json_payload};
                const modelB64 = "{model_b64}";
                
                const container = document.getElementById('canvas-container');
                const tooltip = document.getElementById('sensor-tooltip');
                const loaderText = document.getElementById('loader');

                // ПАЛИТРА ДЛЯ ИНТЕРПОЛЯЦИИ (Радуга Turbo)
                const strainStops = [
                    new THREE.Color("#0022FF"), new THREE.Color("#00E5FF"), new THREE.Color("#00FF44"),
                    new THREE.Color("#FFE600"), new THREE.Color("#FFAA00"), new THREE.Color("#FF5500"), new THREE.Color("#FF0022")
                ];

                function getColorForValue(val, clim) {{
                    if (val === undefined || isNaN(val)) return new THREE.Color(0x334455);
                    const min = clim[0], max = clim[1];
                    let t = (val - min) / ((max - min) || 1.0);
                    t = Math.max(0, Math.min(1, t));
                    const scaled = t * (strainStops.length - 1);
                    const idx = Math.floor(scaled);
                    const fract = scaled - idx;
                    if (idx >= strainStops.length - 1) return strainStops[strainStops.length - 1].clone();
                    const c = new THREE.Color();
                    c.lerpColors(strainStops[idx], strainStops[idx + 1], fract);
                    return c;
                }}

                const scene = new THREE.Scene();
                scene.background = new THREE.Color(0x0A0E17);

                const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 5000);
                const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
                renderer.setSize(container.clientWidth, container.clientHeight);
                renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
                container.appendChild(renderer.domElement);

                const controls = new THREE.OrbitControls(camera, renderer.domElement);
                controls.enableDamping = true; controls.dampingFactor = 0.05;
                controls.minDistance = 0.5; controls.maxDistance = 2500;

                const ambientLight = new THREE.AmbientLight(0xffffff, 1.4);
                scene.add(ambientLight);
                const dirLight1 = new THREE.DirectionalLight(0x00E5FF, 1.6); dirLight1.position.set(60, 100, 80); scene.add(dirLight1);

                const tunnelMeshes = [];
                const binaryStr = atob(modelB64);
                const bytes = new Uint8Array(binaryStr.length);
                for (let i = 0; i < binaryStr.length; i++) {{ bytes[i] = binaryStr.charCodeAt(i); }}

                const gltfLoader = new THREE.GLTFLoader();
                gltfLoader.parse(bytes.buffer, '', function(gltf) {{
                    const model = gltf.scene;
                    scene.add(model);
                    model.updateMatrixWorld(true);
                    loaderText.style.display = 'none';

                    // РАСЧЕТ ИНТЕРПОЛЯЦИИ СВОДА
                    const interpolationSensors = [];
                    for (const rawKey in payload.activeCategoryValues) {{
                        const val = payload.activeCategoryValues[rawKey];
                        const uName = rawKey.toUpperCase();
                        const tun = uName.startsWith("TB") ? "TB" : (uName.startsWith("TA") ? "TA" : "ALL");
                        
                        // Ищем объект датчика в модели, чтобы получить его мировые координаты
                        model.traverse(function(child) {{
                            if (child.isMesh && child.name.toUpperCase() === uName) {{
                                const wPos = new THREE.Vector3();
                                child.getWorldPosition(wPos);
                                interpolationSensors.push({{ pos: wPos, val: val, tun: tun }});
                                
                                // ЦВЕТ САМОГО ДАТЧИКА (БЕЛЫЙ ИЛИ КРАСНЫЙ ЕГО БОЛЬШЕ НЕТ)
                                child.material = new THREE.MeshBasicMaterial({{ color: 0xFFFFFF, side: THREE.DoubleSide }});
                                child.visible = true;
                            }}
                        }});
                    }}

                    // ИНТЕРПОЛЯЦИЯ СВОДА ТОННЕЛЯ
                    const R_INFLUENCE = 48.0;

                    model.traverse(function(child) {{
                        if (child.isMesh) {{
                            const uName = child.name.toUpperCase();
                            const isTunnel = (uName.includes("TUNNEL") || uName.includes("TÜNEL") || uName === "TA" || uName === "TB" || uName.startsWith("TA_") || uName.startsWith("TB_"));

                            if (isTunnel) {{
                                tunnelMeshes.push(child);
                                const geom = child.geometry;
                                if (!geom || !geom.attributes || !geom.attributes.position) return;

                                const posAttr = geom.attributes.position;
                                const colors = new Float32Array(posAttr.count * 3);
                                const localV = new THREE.Vector3();
                                const worldV = new THREE.Vector3();

                                const isTB = uName.includes("TB");
                                const activeTun = isTB ? "TB" : "TA";
                                let pool = interpolationSensors.filter(s => s.tun === activeTun || s.tun === "ALL");
                                if (pool.length === 0) pool = interpolationSensors; // Fallback

                                child.updateMatrixWorld(true);

                                if (pool.length > 0) {{
                                    for (let i = 0; i < posAttr.count; i++) {{
                                        localV.fromBufferAttribute(posAttr, i);
                                        worldV.copy(localV).applyMatrix4(child.matrixWorld);

                                        let totalWeight = 0;
                                        let accumR = 0, accumG = 0, accumB = 0;

                                        for (let j = 0; j < pool.length; j++) {{
                                            const s = pool[j];
                                            const d = worldV.distanceTo(s.pos);
                                            
                                            if (d < R_INFLUENCE) {{
                                                const rNorm = d / R_INFLUENCE;
                                                const wEnvelope = Math.pow(1.0 - Math.pow(rNorm, 1.3), 1.2);
                                                const w = wEnvelope / (Math.pow(d, 1.8) + 0.15);

                                                const c = getColorForValue(s.val, payload.clim);
                                                accumR += c.r * w;
                                                accumG += c.g * w;
                                                accumB += c.b * w;
                                                totalWeight += w;
                                            }}
                                        }}

                                        const idx = i * 3;
                                        if (totalWeight > 0.000001) {{
                                            colors[idx] = accumR / totalWeight;
                                            colors[idx + 1] = accumG / totalWeight;
                                            colors[idx + 2] = accumB / totalWeight;
                                        }} else {{
                                            // Базовый цвет тоннеля
                                            colors[idx] = 0.082; colors[idx + 1] = 0.110; colors[idx + 2] = 0.157;
                                        }}
                                    }}
                                    geom.setAttribute('color', new THREE.BufferAttribute(colors, 3));
                                    geom.attributes.color.needsUpdate = true;
                                }}

                                // БЕЗОПАСНАЯ МАСКА ПРОЗРАЧНОСТИ: Скрывает текстуру внутри цилиндра
                                const shaderMat = new THREE.MeshStandardMaterial({{
                                    vertexColors: true,
                                    transparent: payload.tunnelOpacity < 0.98,
                                    opacity: payload.tunnelOpacity,
                                    roughness: 0.18, metalness: 0.02,
                                    side: THREE.DoubleSide
                                }});

                                // Инжектируем логику маскировки в шейдер
                                shaderMat.onBeforeCompile = (shader) => {{
                                    shader.uniforms.maskRadius = {{ value: 1.95 }}; // Радиус внутренней пустоты
                                    shader.uniforms.maskCenter = {{ value: new THREE.Vector3(0, 0, 0) }}; // Центр тоннеля (упрощение)
                                    shader.uniforms.maskAxis = {{ value: new THREE.Vector3(0, 0, 1) }}; // Ось тоннеля (упрощение)

                                    shader.fragmentShader = `
                                        uniform float maskRadius;
                                        uniform vec3 maskCenter;
                                        uniform vec3 maskAxis;
                                        varying vec3 vWorldPosition;
                                        ${{shader.fragmentShader}}
                                    `.replace(
                                        '#include <dithering_fragment>',
                                        `
                                        #include <dithering_fragment>
                                        
                                        // Расчет расстояния от точки до оси цилиндра
                                        vec3 p = vWorldPosition - maskCenter;
                                        float d = length(p - dot(p, maskAxis) * maskAxis);
                                        
                                        // Скрываем пиксели, если они находятся внутри цилиндра
                                        if (d < maskRadius) discard;
                                        `
                                    );
                                    
                                    // Нужно получить мировые координаты в фрагментном шейдере
                                    shader.vertexShader = shader.vertexShader.replace(
                                        '#include <clipping_planes_pars_vertex>',
                                        `
                                        #include <clipping_planes_pars_vertex>
                                        varying vec3 vWorldPosition;
                                        `
                                    ).replace(
                                        '#include <worldpos_vertex>',
                                        `
                                        #include <worldpos_vertex>
                                        vWorldPosition = (modelMatrix * vec3(position, 1.0)).xyz;
                                        `
                                    );
                                }};

                                child.material = shaderMat;
                                child.material.needsUpdate = true;
                            }}
                        }}
                    }});

                    // ПОЗИЦИОНИРОВАНИЕ КАМЕРЫ (КАК БЫЛО РАНЬШЕ)
                    const savedStateStr = sessionStorage.getItem('threejs_camera_state');
                    if (savedStateStr) {{
                        try {{
                            const st = JSON.parse(savedStateStr);
                            camera.position.set(st.pos[0], st.pos[1], st.pos[2]);
                            controls.target.set(st.target[0], st.target[1], st.target[2]);
                            controls.update();
                        }} catch(e) {{ sessionStorage.removeItem('threejs_camera_state'); }}
                    }} else {{
                        const tunnelBox = new THREE.Box3();
                        if (tunnelMeshes.length > 0) {{
                            tunnelMeshes.forEach(tm => tunnelBox.expandByObject(tm));
                        }} else {{ tunnelBox.setFromObject(model); }}
                        const center = tunnelBox.getCenter(new THREE.Vector3());
                        controls.target.copy(center);
                        camera.position.set(center.x - 30, center.y + 25, center.z + 40);
                        controls.update();
                    }}

                }}, undefined, function(err) {{ loaderText.innerHTML = "Model yüklenirken hata oluştu!"; console.error(err); }});

                window.addEventListener('resize', function() {{
                    camera.aspect = container.clientWidth / container.clientHeight;
                    camera.updateProjectionMatrix();
                    renderer.setSize(container.clientWidth, container.clientHeight);
                }});

                function animate() {{
                    requestAnimationFrame(animate);
                    controls.update();
                    renderer.render(scene, camera);
                }}
                animate();
            </script>
        </body>
        </html>
        """

        st.components.v1.html(threejs_html, height=760, scrolling=False)
