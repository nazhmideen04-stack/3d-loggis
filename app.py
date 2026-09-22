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

# 3 кардинально разные высококонтрастные шкалы с антонимичными полюсами
COLORSCALES = {
    # 1. Çevresel gerinim: Глубокий Синий -> Белый (0) -> Ярко-Красный
    "hoop_bwr": [
        [0.0, "#0010D6"],
        [0.35, "#3388FF"],
        [0.5, "#FFFFFF"],
        [0.65, "#FF4422"],
        [1.0, "#C60000"]
    ],
    # 2. Boyuna gerinim: Изумрудно-Зеленый -> Нейтральный (0) -> Неоновый Пурпурный
    "axial_gvp": [
        [0.0, "#006428"],
        [0.35, "#00E676"],
        [0.5, "#F0F0F0"],
        [0.65, "#E040FB"],
        [1.0, "#6A0080"]
    ],
    # 3. Sıcaklık: Непрерывный тепловой спектр
    "temp_turbo": "Turbo"
}

CATEGORIES = [
    {
        "name": "Othoradial Strains",
        "key": "hoop",
        "tag": "-CS",
        "title": "Çevresel gerinim (CS)",
        "unit": "µm/m",
        "cmap": COLORSCALES["hoop_bwr"]
    },
    {
        "name": "Longitudinal Strains",
        "key": "axial",
        "tag": "-S",
        "title": "Boyuna gerinim (S)",
        "unit": "µm/m",
        "cmap": COLORSCALES["axial_gvp"]
    },
    {
        "name": "Temperature",
        "key": "temp",
        "tag": "-TP",
        "title": "Sıcaklık (TP)",
        "unit": "°C",
        "cmap": COLORSCALES["temp_turbo"]
    },
]

def clean_num(s):
    if not s:
        return np.nan
    s = str(s).replace(",", ".").replace(" ", "").strip()
    m = re.search(r"[-+]?\d+(?:\.\d+)?", s)
    return float(m.group()) if m else np.nan

def parse_date_key(d_str):
    if not d_str:
        return 0.0
    for fmt in ("%d.%m.%Y %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d.%m.%Y %H:%M", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(d_str.strip(), fmt).timestamp()
        except ValueError:
            pass
    return 0.0

@st.cache_data(ttl=300)
def fetch_all_in_memory():
    results = {}
    with sync_playwright() as p:
        browser_args = [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--single-process",
            "--window-size=1920,1080",
        ]
        try:
            browser = p.chromium.launch(headless=True, args=browser_args)
        except Exception:
            os.system("playwright install chromium")
            browser = p.chromium.launch(headless=True, args=browser_args)

        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

        for cat in CATEGORIES:
            page = context.new_page()
            page.goto(URL, timeout=60000, wait_until="domcontentloaded")
            page.wait_for_timeout(4000)

            # 1. Открытие Types
            types_btn = page.get_by_text("Types").first
            types_btn.wait_for(state="visible", timeout=30000)
            types_btn.click()
            page.wait_for_timeout(1000)

            # 2. Выбор категории
            try:
                listbox = page.get_by_role("listbox").first
                listbox.wait_for(state="visible", timeout=5000)
                listbox.select_option(cat["name"])
            except Exception:
                try:
                    page.locator(f"option:has-text('{cat['name']}')").first.click(force=True)
                except Exception:
                    page.get_by_text(cat["name"]).first.click(force=True)

            page.wait_for_timeout(1500)

            try:
                page.keyboard.press("Escape")
            except Exception:
                pass
            page.wait_for_timeout(500)

            # 3. Фильтры: гарантируем выбор самых последних измерений
            combos = page.get_by_role("combobox")
            combos.first.wait_for(state="visible", timeout=20000)

            try:
                combos.nth(1).select_option("TABLE_MOST_RECENT")
            except Exception:
                pass
            page.wait_for_timeout(1500)

            if combos.count() >= 3:
                try:
                    combos.nth(2).select_option("NONE")
                except Exception:
                    pass
                page.wait_for_timeout(800)

            # 4. Чтение таблицы
            table_loc = page.locator("table, [role='grid'], .table").first
            table_loc.wait_for(state="visible", timeout=45000)

            for _ in range(20):
                txt = page.locator("table tbody, [role='rowgroup']").inner_text()
                if cat["tag"] in txt:
                    break
                page.wait_for_timeout(1000)

            # Сбор строго самых свежих данных по timestamp
            sensor_latest = {}
            rows = page.locator("table tbody tr, [role='row']").all()

            for r in rows:
                cols = [td.inner_text().strip() for td in r.locator("td, [role='gridcell']").all()]
                if len(cols) >= 3 and cat["tag"] in cols[1]:
                    d_raw = cols[0]
                    s_name = cols[1]
                    v = clean_num(cols[2])

                    if not np.isnan(v):
                        ts = parse_date_key(d_raw)
                        if s_name not in sensor_latest or ts >= sensor_latest[s_name]["ts"]:
                            sensor_latest[s_name] = {
                                "val": v,
                                "ts": ts,
                                "date_str": d_raw
                            }

            val_map = {k: item["val"] for k, item in sensor_latest.items()}
            latest_date_str = max(sensor_latest.values(), key=lambda x: x["ts"])["date_str"] if sensor_latest else ""

            page.close()
            results[cat["key"]] = {"values": val_map, "date": latest_date_str}

        context.close()
        browser.close()

    return results

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
st.title("LOGGIS 3B TÜNEL İZLEME SİSTEMİ")

col_nav, col_3d = st.columns([1, 4])

with col_nav:
    st.subheader("Kontrol Paneli")
    selected_comp = st.radio(
        "Görüntülenecek Bileşen:",
        options=["hoop", "axial", "temp"],
        format_func=lambda k: next(c["title"] for c in CATEGORIES if c["key"] == k)
    )

    if st.button("🔄 Verileri Yenile (LoggIS)"):
        st.cache_data.clear()
        st.rerun()

with st.spinner("LoggIS verileri taranıyor ve 3B model hesaplanıyor..."):
    all_data = fetch_all_in_memory()

cat_cfg = next(c for c in CATEGORIES if c["key"] == selected_comp)
cur_layer = all_data[selected_comp]
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
    st.write(f"📅 **Son Ölçüm Tarihi:** `{cur_layer['date'] if cur_layer['date'] else 'Canlı'}`")
    st.write(f"📡 **Aktif Sensör:** `{len(v_map)}` adet")
    st.write(f"📊 **Limitler:** `Min: {clim[0]}`, `Maks: {clim[1]} {cat_cfg['unit']}`")

    st.markdown("---")
    selected_sensor = st.selectbox("Sensör Değerini İncele:", options=["Seçiniz..."] + sorted(list(v_map.keys())))
    if selected_sensor != "Seçiniz...":
        st.metric(label=selected_sensor, value=f"{v_map[selected_sensor]:+.2f} {cat_cfg['unit']}")

# --- ПЛОТНЫЙ И ВЫСОКОКОНТРАСТНЫЙ 3D PLOTLY ---
fig = go.Figure()

sensor_x, sensor_y, sensor_z, sensor_text, sensor_colors = [], [], [], [], []

for ti, tun in enumerate(("TA", "TB")):
    off_x = (ti - 0.5) * SP
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
        lighting=dict(
            ambient=0.98,
            diffuse=0.3,
            roughness=0.9,
            specular=0.0
        ),
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

if sensor_x:
    fig.add_trace(go.Scatter3d(
        x=sensor_x,
        y=sensor_y,
        z=sensor_z,
        mode="markers",
        marker=dict(
            size=6,
            color=sensor_colors,
            symbol="circle",
            opacity=1.0,
            line=dict(color="#000000", width=1.5)
        ),
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
        camera=dict(
            eye=dict(x=-1.5, y=1.6, z=1.0),
            center=dict(x=0, y=0, z=0)
        )
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

with col_3d:
    st.plotly_chart(fig, use_container_width=True, config=config)
