import os
import re
import base64
from datetime import datetime
import numpy as np
from scipy.interpolate import RBFInterpolator
import plotly.graph_objects as go
import streamlit as st
from playwright.sync_api import sync_playwright

st.set_page_config(page_title="LOGGIS 3B", layout="wide")

URL = "https://loggis2.com/?company-id=20ce6d9f-398b-43b3-a452-3580dae39122&project-id=2d381d12-d966-4c90-a7c8-c90d6f758ae0&token-id=6e73d15f-0b2f-4d93-a152-3464f7450e50"

LOGO_PATH = "logo.jpg" if os.path.exists("logo.jpg") else "logo.png"

# Фирменный стиль DESTECH (без темно-синего фона страницы)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;600;700&family=Syne:wght@700;800&display=swap');

    html, body, [class*="css"], p, span, label, .stMarkdown {
        font-family: 'Chakra Petch', sans-serif !important;
        color: #E2ECF7;
    }

    h1, h2, h3 {
        font-family: 'Syne', sans-serif !important;
        font-weight: 800 !important;
        letter-spacing: 1.5px !important;
        text-transform: uppercase;
        color: #FFFFFF !important;
    }

    /* Убираем серый фон у инлайн-кода (бэктиков ` `) */
    code {
        background-color: transparent !important;
        color: #FFFFFF !important;
        border: none !important;
        padding: 0 !important;
        font-weight: 600 !important;
    }

    .destech-badge {
        font-family: 'Syne', sans-serif;
        font-size: 16px;
        font-weight: 800;
        letter-spacing: 2px;
        background: linear-gradient(90deg, #1E9AD6 0%, #1858BA 100%);
        color: #000000;
        padding: 6px 18px;
        border-radius: 6px;
        display: inline-block;
        box-shadow: 0 4px 14px rgba(30, 154, 214, 0.35);
    }

    div.stButton > button {
        background: linear-gradient(90deg, #1E9AD6 0%, #1858BA 100%) !important;
        color: #FFFFFF !important;
        font-family: 'Chakra Petch', sans-serif !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 6px !important;
        transition: all 0.3s ease !important;
    }
    div.stButton > button:hover {
        box-shadow: 0 0 15px rgba(30, 154, 214, 0.7) !important;
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)

# Считываем логотип в Base64 для точного совмещения по высоте с заголовком
logo_b64 = ""
if os.path.exists(LOGO_PATH):
    with open(LOGO_PATH, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()

logo_tag = f'<img src="data:image/jpeg;base64,{logo_b64}" style="width: 200px; height: auto; display: block; margin: 0; opacity: 0.55; border-radius: 4px;" alt="DESTECH">' if logo_b64 else '<span class="destech-badge">DESTECH</span>'

# Единая строка: заголовок и логотип на строго одной вертикальной координате
st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-top: -20px; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid rgba(255, 255, 255, 0.1);">
    <div style="display: flex; flex-direction: column; justify-content: center; margin: 0; padding: 0;">
        <h1 style="margin: 0 !important; padding: 0 !important; font-size: 32px !important; line-height: 1.1 !important;">LOGGIS 3B</h1>
        <div style="color: #1E9AD6; font-weight: 600; font-size: 13px; letter-spacing: 1px; margin-top: 3px;">SENSÖR CANLI TAKİP SİSTEMİ</div>
    </div>
    <div style="display: flex; align-items: center; margin: 0; padding: 0;">
        {logo_tag}
    </div>
</div>
""", unsafe_allow_html=True)

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

def parse_robust_timestamp(d_str):
    if not d_str:
        return 0.0
    nums = [int(n) for n in re.findall(r"\d+", str(d_str))]
    if len(nums) < 3:
        return 0.0
    try:
        if nums[0] > 1900:
            year, month, day = nums[0], nums[1], nums[2]
            hour = nums[3] if len(nums) > 3 else 0
            minute = nums[4] if len(nums) > 4 else 0
            second = nums[5] if len(nums) > 5 else 0
        elif nums[2] > 1900:
            day, month, year = nums[0], nums[1], nums[2]
            hour = nums[3] if len(nums) > 3 else 0
            minute = nums[4] if len(nums) > 4 else 0
            second = nums[5] if len(nums) > 5 else 0
        else:
            return 0.0
        return datetime(year, month, day, hour, minute, second).timestamp()
    except Exception:
        return 0.0

# ВНИМАНИЕ: Декоратор @st.cache_data убран намеренно, чтобы не застревал пустой кэш!
def fetch_category_data(cat_key, reload_seed=0):
    cat = CATEGORIES[cat_key]
    val_map = {}
    latest_date_str = ""
    screenshot_b64 = ""
    debug_msg = ""

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
        except Exception as e_launch:
            return {
                "values": {},
                "date": "",
                "screenshot": "",
                "debug": f"Критическая ошибка запуска браузера Chromium: {e_launch}. Проверьте packages.txt!"
            }

        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="fr-FR",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            # 1. Загрузка страницы
            page.goto(URL, timeout=60000, wait_until="networkidle")
            page.wait_for_timeout(3000)

            # 2. Клик по вкладке Types
            try:
                page.locator("text='Types'").first.click(timeout=8000)
                page.wait_for_timeout(800)
            except Exception as e_tab:
                debug_msg += f"[Вкладка Types: {e_tab}] "

            # 3. Клик по нужной категории (Temperature, Longitudinal strains, etc.)
            try:
                # Пытаемся кликнуть по тексту элемента в списке
                cat_el = page.locator(f"text='{cat['name']}'").first
                cat_el.click(timeout=8000)
                page.wait_for_timeout(1500)
            except Exception:
                # Запасной клик через JavaScript
                page.evaluate(f"""() => {{
                    const els = Array.from(document.querySelectorAll('*'));
                    const target = els.find(e => e.textContent && e.textContent.trim().toLowerCase() === '{cat['name']}'.toLowerCase() && e.children.length === 0);
                    if (target) {{
                        ['mousedown', 'mouseup', 'click'].forEach(evt => {{
                            target.dispatchEvent(new MouseEvent(evt, {{ bubbles: true, cancelable: true }}));
                        }});
                    }}
                }}""")
                page.wait_for_timeout(2000)

            # ДЕЛАЕМ СКРИНШОТ
            try:
                img_bytes = page.screenshot()
                screenshot_b64 = base64.b64encode(img_bytes).decode("utf-8")
            except Exception as e_scr:
                debug_msg += f"[Скриншот не сделан: {e_scr}] "

            # 4. Проверяем наличие таблицы и считываем данные
            extracted = page.evaluate("""(tag) => {
                const table = document.querySelector('table');
                if (!table) return null;

                // Заголовки (датчики)
                const trs = Array.from(table.querySelectorAll('tr'));
                let headerCells = [];
                for (const tr of trs) {
                    const cells = Array.from(tr.querySelectorAll('th, td')).map(c => c.innerText.trim());
                    if (cells.some(c => c.includes(tag) || c.includes('TA-') || c.includes('TB-'))) {
                        headerCells = cells;
                        break;
                    }
                }
                if (headerCells.length === 0 && trs.length > 0) {
                    headerCells = Array.from(trs[0].querySelectorAll('th, td')).map(c => c.innerText.trim());
                }

                // Первая строка данных (самый свежий замер)
                const tbody = table.querySelector('tbody') || table;
                const bodyRows = Array.from(tbody.querySelectorAll('tr'));
                let dataCells = [];
                for (const r of bodyRows) {
                    const cells = Array.from(r.querySelectorAll('td')).map(c => c.innerText.trim());
                    if (cells.length > 1 && (cells[0].includes('/') || cells[0].includes(':'))) {
                        dataCells = cells;
                        break;
                    }
                }

                return { headers: headerCells, values: dataCells };
            }""", cat["tag"])

            if extracted and extracted.get("values") and extracted.get("headers"):
                headers = extracted["headers"]
                values = extracted["values"]
                latest_date_str = values[0]

                for h, v_str in zip(headers[1:], values[1:]):
                    if cat["tag"] in h or "TA-" in h or "TB-" in h:
                        m = re.search(r"(T[AB]-[A-Za-z0-9\-]+)", h)
                        s_name = m.group(1) if m else h.split()[0].strip()
                        v = clean_num(v_str)
                        if not np.isnan(v):
                            val_map[s_name] = v
            else:
                debug_msg += "[Таблица с данными пока не обнаружена в DOM] "

        except Exception as e_main:
            debug_msg += f"[Общая ошибка Playwright: {e_main}] "
        finally:
            browser.close()

    return {
        "values": val_map,
        "date": latest_date_str,
        "screenshot": screenshot_b64,
        "debug": debug_msg
    }
# Geometri Tanımları
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
        rbf = RBFInterpolator(wrapped, np.concatenate([e, e, e]), kernel="thin_plate_spline", smoothing=1.0)
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

with col_nav:
    st.subheader("Kontrol Panelİ")
    selected_comp = st.radio(
        "Görüntülenecek Bileşen:",
        options=["hoop", "axial", "temp"],
        format_func=lambda k: CATEGORIES[k]["title"]
    )

    if st.button("Verileri Yenile"):
        st.cache_data.clear()
        st.rerun()

cat_cfg = CATEGORIES[selected_comp]

with st.spinner(f"{cat_cfg['title']} verisi LoggIS üzerinden alınıyor..."):
    cur_layer = fetch_category_data(selected_comp)

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
    st.write("📅 **En Son Veri Zamanı:**")
    st.write(f"{cur_layer['date'] if cur_layer['date'] else 'Bilinmiyor'}")
    st.write("📡 **Aktif Sensör Sayısı:**")
    st.write(f"{len(v_map)}")
    st.write("📊 **Skala Limitleri:**")
    st.write(f"Min: {clim[0]} | Maks: {clim[1]} {cat_cfg['unit']}")

    st.markdown("---")
    selected_sensor = st.selectbox("Sensör Değerini İncele:", options=["Seçiniz..."] + sorted(list(v_map.keys())))
    if selected_sensor != "Seçiniz...":
        st.metric(label=selected_sensor, value=f"{v_map[selected_sensor]:+.2f} {cat_cfg['unit']}")

# --- 3B PLOTLY SAHNESİ ---
with col_3d:
    if not v_map:
        st.error("⚠️ LoggIS sisteminden veri alınamadı.")
        
        # Показываем детальный текст ошибки
        if cur_layer.get("debug"):
            st.code(cur_layer["debug"])
            
        # Показываем живой скриншот страницы
        if cur_layer.get("screenshot"):
            st.write("📸 **Снимок страницы LoggIS в момент работы скрипта:**")
            st.image(f"data:image/png;base64,{cur_layer['screenshot']}", use_container_width=True)
    else:
        # Ваш 3D Plotly код...
        # 3B Plotly çizim kodları...
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
                sensor_colors.append("#FFFF00" if n == selected_sensor else "#FFFFFF")

        # 3D метки TA и TB
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
                color="#1E9AD6"
            ),
            hoverinfo="none",
            showlegend=False
        ))

        # Маркеры сенсоров
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
            paper_bgcolor="#0E1117",
            scene=dict(
                xaxis=dict(showbackground=False, showgrid=True, gridcolor="#262730", zeroline=False, title="", showticklabels=False),
                yaxis=dict(showbackground=False, showgrid=True, gridcolor="#262730", zeroline=False, title="", showticklabels=False),
                zaxis=dict(showbackground=False, showgrid=True, gridcolor="#262730", zeroline=False, title="Boyuna (Z)", color="#1E9AD6"),
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
