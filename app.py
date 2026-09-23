import os
import re
import sys
import base64
import subprocess
from datetime import datetime
import numpy as np
from scipy.interpolate import RBFInterpolator
import plotly.graph_objects as go
import streamlit as st
from playwright.sync_api import sync_playwright

st.set_page_config(page_title="LOGGIS 3B", layout="wide")

URL = "https://loggis2.com/?company-id=20ce6d9f-398b-43b3-a452-3580dae39122&project-id=2d381d12-d966-4c90-a7c8-c90d6f758ae0&token-id=6e73d15f-0b2f-4d93-a152-3464f7450e50"

LOGO_PATH = "logo.jpg" if os.path.exists("logo.jpg") else "logo.png"

# Фирменный стиль DESTECH: темный фон, крупные пункты выбора и синий кружок без лишнего неона
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
        text-shadow: none !important;
    }

    [data-testid="stMetricValue"], .neon-data {
        color: #00C8E6 !important;
        font-weight: 700 !important;
        text-shadow: none !important;
        box-shadow: none !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #8397AD !important;
        font-size: 13px !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }


    /* Заголовок "Görüntülenecek Bileşen:" (делаем его маленьким и аккуратным) */
    div[data-testid="stRadio"] > label p,
    div[data-testid="stRadio"] > label {
        font-size: 15px !important;  /* <--- ВОТ ЗДЕСЬ МЕНЯТЬ РАЗМЕР ЗАГОЛОВКА */
        font-weight: 600 !important;
        color: #8397AD !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 6px !important;
    }

    /* Сами пункты выбора (Çevresel gerinim, Boyuna gerinim, Sıcaklık) */
    div[data-testid="stRadio"] div[role="radiogroup"] label p {
        font-size: 21px !important;  /* <--- ВОТ ЗДЕСЬ МЕНЯТЬ РАЗМЕР САМИХ ВАРИАНТОВ */
        font-weight: 700 !important;
        color: #E6F0FA !important;
        line-height: 1.4 !important;
        text-shadow: none !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] > label {
        margin-bottom: 14px !important;
        cursor: pointer !important;
        display: flex !important;
        align-items: center !important;
    }

    /* Принудительный синий цвет активного кружка через фильтр */
    div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) div:first-child {
        filter: hue-rotate(185deg) saturate(2) !important;
    }

    /* Увеличение размера самого кружка выбора */
    div[data-testid="stRadio"] div[role="radiogroup"] label > div:first-child {
        transform: scale(1.25) !important;
        transform-origin: center center !important;
        margin-right: 14px !important;
    }

    div[data-baseweb="select"] {
        background-color: #0E182A !important;
        border: 1px solid rgba(0, 200, 230, 0.4) !important;
        border-radius: 6px !important;
        box-shadow: none !important;
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
        box-shadow: none !important;
    }

 /* Кнопка "Verileri Yenile" без неона, градиента и свечения */
    div.stButton > button {
        background-color: #0E2238 !important;
        color: #00C8E6 !important;
        font-family: 'Chakra Petch', sans-serif !important;
        font-size: 15px !important;
        font-weight: 700 !important;
        border: 1px solid rgba(0, 200, 230, 0.4) !important;
        border-radius: 6px !important;
        padding: 9px 20px !important;
        box-shadow: none !important;
        text-shadow: none !important;
        transition: background-color 0.2s ease, border-color 0.2s ease !important;
    }

    div.stButton > button:hover {
        background-color: #132E4C !important;
        border-color: #00C8E6 !important;
        color: #FFFFFF !important;
        box-shadow: none !important;
        text-shadow: none !important;
        transform: none !important;
    }

    div.stButton > button:active, div.stButton > button:focus {
        background-color: #0E2238 !important;
        border-color: #00C8E6 !important;
        box-shadow: none !important;
    }
</style>
""", unsafe_allow_html=True)

logo_b64 = ""
if os.path.exists(LOGO_PATH):
    with open(LOGO_PATH, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()

logo_tag = f'<img src="data:image/jpeg;base64,{logo_b64}" style="width: 200px; height: auto; display: block; margin: 0; opacity: 0.75; border-radius: 4px;" alt="DESTECH">' if logo_b64 else '<span class="destech-badge">DESTECH</span>'

# --- ИНТЕРФЕЙС STREAMLIT ---

# 1. Сначала подгружаем все данные в кэш
with st.spinner("Tüm sensör verileri (CS, S, TP) LoggIS üzerinden tek seferde alınıyor..."):
    all_data = fetch_all_categories_data()

# 2. ОБЯЗАТЕЛЬНО: объявляем колонки col_nav и col_3d
col_nav, col_3d = st.columns([1, 4])

# 3. И только после этого заходим внутрь col_nav
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

    # Стилизованные плашки со значениями
    st.markdown("---")
    
    st.markdown("<div style='color: #8397AD; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px;'>📅 En Son Veri Zamanı</div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style="
            background-color: #0E182A;
            border: 1px solid rgba(0, 200, 230, 0.35);
            border-radius: 6px;
            padding: 8px 12px;
            color: #00C8E6;
            font-size: 16px;
            font-weight: 700;
            letter-spacing: 0.5px;
            margin-bottom: 12px;
        ">
            {all_data.get(selected_comp, {}).get('date', 'Bilinmiyor')}
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='color: #8397AD; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px;'>📡 Aktif Sensör Sayısı</div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style="
            background-color: #0E182A;
            border: 1px solid rgba(0, 200, 230, 0.35);
            border-radius: 6px;
            padding: 8px 12px;
            color: #00C8E6;
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 12px;
        ">
            {len(v_map)}
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='color: #8397AD; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px;'>📊 Skala Limitleri</div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style="
            background-color: #0E182A;
            border: 1px solid rgba(0, 200, 230, 0.35);
            border-radius: 6px;
            padding: 8px 12px;
            color: #00C8E6;
            font-size: 15px;
            font-weight: 700;
            margin-bottom: 12px;
        ">
            Min: {clim[0]} | Maks: {clim[1]} {cat_cfg['unit']}
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

COLORSCALES = {
    "hoop_bwr": [
        [0.0, "#1858BA"],
        [0.35, "#1E9AD6"],
        [0.5, "#FFFFFF"],
        [0.65, "#FF4422"],
        [1.0, "#C60000"]
    ],
    "axial_gvp": [
        [0.0, "#006428"],
        [0.35, "#00E676"],
        [0.5, "#F0F0F0"],
        [0.65, "#E040FB"],
        [1.0, "#6A0080"]
    ],
    "temp_turbo": "Turbo"
}

CATEGORIES = {
    "hoop": {"name": "Othoradial Strains", "tag": "-CS", "title": "Çevresel gerinim (CS)", "unit": "µm/m", "cmap": COLORSCALES["hoop_bwr"]},
    "axial": {"name": "Longitudinal Strains", "tag": "-S", "title": "Boyuna gerinim (S)", "unit": "µm/m", "cmap": COLORSCALES["axial_gvp"]},
    "temp": {"name": "Temperature", "tag": "-TP", "title": "Sıcaklık (TP)", "unit": "°C", "cmap": COLORSCALES["temp_turbo"]},
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

# Единая пакетная загрузка всех типов измерений за один проход браузера
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

        # Открываем Types
        page.get_by_text("Types").click()
        page.wait_for_timeout(800)

        # Устанавливаем фильтры один раз
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

        # Последовательно считываем каждую категорию без перезапуска страницы
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

GEOMETRY = {
    "tunnel_radius_m": 3.0,
    "tunnel_spacing_m": 15.0,
    "cs_angle_deg": {
        ("R", "M1"): 0.0, ("R", "M2"): 45.0, ("R", "M3"): 90.0,
        ("R", "M4"): 135.0, ("R", "M5"): 180.0,
        ("L", "M1"): 225.0, ("L", "M2"): 270.0, ("L", "M3"): 315.0,
    },
    "cs_chainage_m": {"CS1": 0.0, "CS2": 30.0, "CS3": 60.0, "CS4": 90.0},
    "s_line_angle_deg": {"L1": 270.0, "L2": 90.0},
    "s_chainage_m": {
        ("S1", "M1"): 0.0, ("S1", "M2"): 5.0, ("S1", "M3"): 10.0,
        ("S1", "M4"): 15.0, ("S1", "M5"): 20.0,
        ("S2", "M1"): 35.0, ("S2", "M2"): 40.0, ("S2", "M3"): 45.0,
        ("S2", "M4"): 50.0, ("S2", "M5"): 55.0,
        ("S3", "M1"): 70.0, ("S3", "M2"): 75.0, ("S3", "M3"): 80.0,
        ("S3", "M4"): 85.0, ("S3", "M5"): 90.0,
    },
}

R = GEOMETRY["tunnel_radius_m"]
SP = GEOMETRY["tunnel_spacing_m"]
angle_scale = 2 * np.pi * R / 360.0

def parse_channel(name: str):
    parts = name.strip().split("-")
    if len(parts) != 4 or parts[0] not in ("TA", "TB"):
        return None
    return parts[0], ("CS" if parts[1].startswith("CS") else "S"), parts[1], parts[2], parts[3]

def position(name: str):
    parsed = parse_channel(name)
    if not parsed:
        return None
    _, kind, section, place, point = parsed
    if kind == "CS":
        if point == "TP":
            angles = [v for (side, _), v in GEOMETRY["cs_angle_deg"].items() if side == place]
            return GEOMETRY["cs_chainage_m"][section], float(np.mean(angles))
        return (GEOMETRY["cs_chainage_m"][section], GEOMETRY["cs_angle_deg"].get((place, point)))
    if point == "TP":
        chain = [v for (sec, _), v in GEOMETRY["s_chainage_m"].items() if sec == section]
        return float(np.mean(chain)), GEOMETRY["s_line_angle_deg"].get(place)
    return (GEOMETRY["s_chainage_m"].get((section, point)), GEOMETRY["s_line_angle_deg"].get(place))

def patches_for(comp, pos):
    x0, x1 = float(pos[:, 0].min()), float(pos[:, 0].max())
    if comp == "axial":
        return [{
            "angles": list(np.linspace(ang - 25.0, ang + 25.0, 4)),
            "chainage": list(np.linspace(x0, x1, 24)),
            "closed": False
        } for ang in sorted({float(a) for a in pos[:, 1]} if pos.ndim > 1 else [])]
    return [{
        "angles": list(np.linspace(0.0, 360.0, 24, endpoint=False)),
        "chainage": list(np.linspace(x0, x1, 24 if comp == "temp" else 18)),
        "closed": True
    }]

def build_operator(names, patches):
    pos = np.array([position(n) for n in names])
    rows = []
    for p in patches:
        for a in p["angles"]:
            for c in p["chainage"]:
                rows.append([c, a])
    grid = np.array(rows, dtype=np.float32)
    query = np.column_stack([grid[:, 0], grid[:, 1] * angle_scale])

    if len(names) < 3:
        W = np.full((query.shape[0], len(names)), 1.0 / max(len(names), 1), dtype=np.float32)
        return pos, W

    wrapped = np.vstack([
        np.column_stack([pos[:, 0], pos[:, 1] - 360.0]),
        pos,
        np.column_stack([pos[:, 0], pos[:, 1] + 360.0]),
    ])
    wrapped[:, 1] *= angle_scale
    
    W = np.empty((query.shape[0], len(names)), dtype=np.float32)
    for j in range(len(names)):
        e = np.zeros(len(names))
        e[j] = 1.0
        rbf = RBFInterpolator(wrapped, np.concatenate([e, e, e]), kernel="linear", smoothing=1.0)
        W[:, j] = rbf(query)
    return pos, W

def build_mesh_data(patches, offset_x):
    pts, triangles = [], []
    offset = 0
    for p in patches:
        nA, nC = len(p["angles"]), len(p["chainage"])
        for a in range(nA):
            ang = np.radians(p["angles"][a])
            for c in range(nC):
                pts.append([offset_x + R * np.sin(ang), R * np.cos(ang), p["chainage"][c] - 45.0])
        num_rows = nA if p["closed"] else nA - 1
        for a in range(num_rows):
            next_a = (a + 1) % nA
            for c in range(nC - 1):
                p0 = offset + a * nC + c
                p1 = offset + a * nC + c + 1
                p2 = offset + next_a * nC + c
                p3 = offset + next_a * nC + c + 1
                triangles.append([p0, p2, p1])
                triangles.append([p1, p2, p3])
        offset += nA * nC
    return np.array(pts, dtype=np.float32), np.array(triangles, dtype=np.int32)

# --- ИНТЕРФЕЙС STREAMLIT ---
col_nav, col_3d = st.columns([1, 4])

# Подгрузка всех данных сразу в кэш
with st.spinner("Tüm sensör verileri (CS, S, TP) LoggIS üzerinden tek seferde alınıyor..."):
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

# --- 3B PLOTLY SAHNESİ ---
with col_3d:
    if not v_map:
        st.warning("⚠️ LoggIS sisteminden güncel veri alınamadı. Lütfen 'Verileri Yenile' butonunu deneyiniz.")
    else:
        fig = go.Figure()
        sensor_x, sensor_y, sensor_z, sensor_text, sensor_colors = [], [], [], [], []
        label_x, label_y, label_z, label_text = [], [], [], []

        for ti, tun in enumerate(("TA", "TB")):
            off_x = (ti - 0.5) * SP
            label_x.append(off_x)
            label_y.append(R + 3.8)
            label_z.append(-49.0)
            label_text.append(f"  {tun}  ")

            names = [c for c in v_map if c.startswith(tun + "-") and position(c) is not None and None not in position(c)]
            if not names:
                continue

            pos = np.array([position(n) for n in names])
            patches = patches_for(selected_comp, pos)
            pos, W = build_operator(names, patches)
            pts, tris = build_mesh_data(patches, off_x)

            cur_vals = np.array([v_map.get(c, 0.0) for c in names], dtype=np.float32)
            scalars = W @ cur_vals

            fig.add_trace(go.Mesh3d(
                x=pts[:, 0],
                y=pts[:, 1],
                z=pts[:, 2],
                i=tris[:, 0],
                j=tris[:, 1],
                k=tris[:, 2],
                intensity=scalars,
                colorscale=cat_cfg["cmap"],
                cmin=clim[0],
                cmax=clim[1],
                opacity=1.0,
                name=f"Tünel {tun}",
                lighting=dict(ambient=0.98, diffuse=0.3, roughness=0.9, specular=0.0),
                colorbar=dict(
                    title=dict(text=f"[{cat_cfg['unit']}]", side="top"),
                    thickness=16,
                    len=0.7,
                    x=0.98,
                    tickfont=dict(color="#FFF", size=11)
                ) if ti == 0 else None,
                showscale=(ti == 0),
                hoverinfo="skip"
            ))

            for n, pt in zip(names, pos):
                ang = np.radians(pt[1])
                sx = off_x + (R + 0.12) * np.sin(ang)
                sy = (R + 0.12) * np.cos(ang)
                sz = pt[0] - 45.0
                sensor_x.append(sx)
                sensor_y.append(sy)
                sensor_z.append(sz)
                val_txt = f"{v_map.get(n, np.nan):+.2f} {cat_cfg['unit']}"
                sensor_text.append(f"<b>{n}</b><br>Değer: {val_txt}")
                sensor_colors.append("#00C8E6" if n == selected_sensor else "#FFFFFF")

        fig.add_trace(go.Scatter3d(
            x=label_x,
            y=label_y,
            z=label_z,
            mode="text",
            text=label_text,
            textposition="top center",
            textfont=dict(
                family="Syne, Chakra Petch, sans-serif",
                size=28,
                color="#00C8E6"
            ),
            hoverinfo="none",
            showlegend=False
        ))

        if sensor_x:
            fig.add_trace(go.Scatter3d(
                x=sensor_x,
                y=sensor_y,
                z=sensor_z,
                mode="markers",
                marker=dict(size=6, color=sensor_colors, symbol="circle", opacity=1.0, line=dict(color="#000000", width=1.5)),
                text=sensor_text,
                hoverinfo="text",
                name="Sensörler"
            ))

        fig.update_layout(
            dragmode="orbit",
            paper_bgcolor="#0A0E17",
            plot_bgcolor="#0A0E17",
            scene=dict(
                xaxis=dict(showbackground=False, showgrid=True, gridcolor="#172238", zeroline=False, title="", showticklabels=False),
                yaxis=dict(showbackground=False, showgrid=True, gridcolor="#172238", zeroline=False, title="", showticklabels=False),
                zaxis=dict(showbackground=False, showgrid=True, gridcolor="#172238", zeroline=False, title="Boyuna (Z)", color="#00C8E6"),
                aspectratio=dict(x=1.3, y=0.5, z=2.2),
                camera=dict(eye=dict(x=-1.5, y=1.6, z=1.0), center=dict(x=0, y=0, z=0))
            ),
            margin=dict(l=0, r=0, b=0, t=10),
            height=720,
            showlegend=False
        )

        config = {
            "scrollZoom": True,
            "displayModeBar": True,
            "modeBarButtonsToRemove": ["resetCameraDefault3d", "hoverClosest3d"],
            "displaylogo": False
        }

        st.plotly_chart(fig, use_container_width=True, config=config)
