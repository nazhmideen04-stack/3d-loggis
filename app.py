import os
import re
from datetime import datetime
import numpy as np
from scipy.interpolate import RBFInterpolator
import plotly.graph_objects as go
import streamlit as st
from playwright.sync_api import sync_playwright

st.set_page_config(page_title="LOGGIS 3B", layout="wide")

URL = "https://loggis2.com/?company-id=20ce6d9f-398b-43b3-a452-3580dae39122&project-id=2d381d12-d966-4c90-a7c8-c90d6f758ae0&token-id=6e73d15f-0b2f-4d93-a152-3464f7450e50"

LOGO_PATH = "logo.png"

# Стили для аккуратной шапки и полупрозрачности логотипа
st.markdown("""
<style>
    [data-testid="stImage"] img {
        opacity: 0.75;
        transition: opacity 0.3s ease;
    }
    [data-testid="stImage"] img:hover {
        opacity: 1.0;
    }
    .header-badge {
        font-family: sans-serif;
        font-weight: 800;
        font-size: 18px;
        letter-spacing: 2px;
        color: rgba(255, 255, 255, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 4px 12px;
        border-radius: 6px;
        display: inline-block;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Верхняя брендовая строка
col_head_title, col_head_logo = st.columns([4, 1])

with col_head_title:
    st.markdown("<h1 style='margin-bottom: 0px;'>LOGGIS 3B</h1>", unsafe_allow_html=True)

with col_head_logo:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=150)
    else:
        st.markdown("<div style='text-align: right;'><span class='header-badge'>LOGGIS</span></div>", unsafe_allow_html=True)

COLORSCALES = {
    "hoop_bwr": [
        [0.0, "#0010D6"],
        [0.35, "#3388FF"],
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

@st.cache_data(ttl=180)
def fetch_category_data(cat_key):
    cat = CATEGORIES[cat_key]
    with sync_playwright() as p:
        browser_args = [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--single-process",
            "--blink-settings=imagesEnabled=false",
        ]
        try:
            browser = p.chromium.launch(headless=True, args=browser_args)
        except Exception:
            os.system("playwright install chromium")
            browser = p.chromium.launch(headless=True, args=browser_args)

        context = browser.new_context(
            viewport={"width": 1600, "height": 900},
            timezone_id="Europe/Istanbul",
            locale="tr-TR",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media", "font", "stylesheet"] else route.continue_())

        page.goto(URL, timeout=40000, wait_until="domcontentloaded")

        types_btn = page.get_by_text("Types").first
        types_btn.wait_for(state="visible", timeout=20000)
        types_btn.click()
        page.wait_for_timeout(300)

        try:
            listbox = page.get_by_role("listbox").first
            listbox.wait_for(state="visible", timeout=3000)
            listbox.select_option(cat["name"])
        except Exception:
            try:
                page.locator(f"option:has-text('{cat['name']}')").first.click(force=True)
            except Exception:
                page.get_by_text(cat["name"]).first.click(force=True)

        page.wait_for_timeout(400)
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass

        combos = page.get_by_role("combobox")
        combos.first.wait_for(state="visible", timeout=15000)
        try:
            combos.first.select_option("ALL")
        except Exception:
            pass
        page.wait_for_timeout(400)

        try:
            combos.nth(1).select_option("TABLE_MOST_RECENT")
        except Exception:
            pass
        page.wait_for_timeout(500)

        table_loc = page.locator("table, [role='grid'], .table").first
        table_loc.wait_for(state="visible", timeout=25000)

        raw_table_data = page.evaluate("""() => {
            const rows = Array.from(document.querySelectorAll('table tbody tr, [role="row"]'));
            return rows.map(r => Array.from(r.querySelectorAll('td, [role="gridcell"]')).map(c => c.innerText.trim()))
                       .filter(c => c.length >= 3);
        }""")

        browser.close()

    sensor_best = {}
    for idx, cols in enumerate(raw_table_data):
        if cat["tag"] in cols[1]:
            d_raw = cols[0]
            s_name = cols[1]
            v = clean_num(cols[2])
            if not np.isnan(v):
                ts = parse_robust_timestamp(d_raw)
                if s_name not in sensor_best:
                    sensor_best[s_name] = (ts, v, d_raw, idx)
                else:
                    prev_ts, _, _, prev_idx = sensor_best[s_name]
                    if ts > prev_ts or (ts == prev_ts and idx > prev_idx):
                        sensor_best[s_name] = (ts, v, d_raw, idx)

    val_map = {s: item[1] for s, item in sensor_best.items()}
    latest_date_str = max(sensor_best.values(), key=lambda x: x[0])[2] if sensor_best else ""

    return {"values": val_map, "date": latest_date_str}

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
    st.subheader("Kontrol Paneli")
    selected_comp = st.radio(
        "Görüntülenecek Bileşen:",
        options=["hoop", "axial", "temp"],
        format_func=lambda k: CATEGORIES[k]["title"]
    )

    if st.button("🔄 Verileri Yenile (LoggIS)"):
        st.cache_data.clear()
        st.rerun()

cat_cfg = CATEGORIES[selected_comp]

with st.spinner(f"{cat_cfg['title']} verisi taranıyor..."):
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
    st.write(f"📅 **En Son Veri Zamanı:**")
    st.info(f"🕒 `{cur_layer['date'] if cur_layer['date'] else 'Bilinmiyor'}`")
    st.write(f"📡 **Aktif Sensör Sayısı:** `{len(v_map)}` adet")
    st.write(f"📊 **Skala Limitleri:** `Min: {clim[0]}`, `Maks: {clim[1]} {cat_cfg['unit']}`")

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
                sensor_colors.append("#FFFF00" if n == selected_sensor else "#FFFFFF")

        # 3D метки TA и TB
        fig.add_trace(go.Scatter3d(
            x=label_x,
            y=label_y,
            z=label_z,
            mode="text",
            text=label_text,
            textposition="top center",
            textfont=dict(family="Trebuchet MS, Arial, sans-serif", size=26, color="#FFFFFF"),
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
            paper_bgcolor="#101216",
            scene=dict(
                xaxis=dict(showbackground=False, showgrid=True, gridcolor="#252830", zeroline=False, title="", showticklabels=False),
                yaxis=dict(showbackground=False, showgrid=True, gridcolor="#252830", zeroline=False, title="", showticklabels=False),
                zaxis=dict(showbackground=False, showgrid=True, gridcolor="#252830", zeroline=False, title="Boyuna (Z)", color="#888"),
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
