import os
import re
import sys
import subprocess
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from scipy.interpolate import RBFInterpolator
from playwright.sync_api import sync_playwright

st.set_page_config(layout="wide")

URL = "https://loggis2.com/?company-id=20ce6d9f-398b-43b3-a452-3580dae39122&project-id=2d381d12-d966-4c90-a7c8-c90d6f758ae0&token-id=6e73d15f-0b2f-4d93-a152-3464f7450e50"

CATEGORIES = {
    "temperature": {"name": "Temperature", "tag": "-TP", "unit": "°C", "color_scale": "Turbo"},
    "longitudinal": {"name": "Longitudinal strains", "tag": "-L", "unit": "µε", "color_scale": "RdBu_r"},
    "othoradial": {"name": "Othoradial strains", "tag": "-CS", "unit": "µε", "color_scale": "Viridis"},
}

angle_scale = 1.0

def clean_num(s):
    if not s:
        return np.nan
    try:
        s_clean = s.strip().replace(" ", "").replace(",", ".")
        return float(re.findall(r"[-+]?\d*\.?\d+", s_clean)[0])
    except Exception:
        return np.nan

def ensure_playwright_installed():
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    except Exception:
        pass

def fetch_category_data(cat_key, reload_seed=0):
    cat = CATEGORIES[cat_key]
    val_map = {}
    latest_date_str = ""

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
            locale="fr-FR",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            page.goto(URL, timeout=60000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            # 1. Переход на Types
            page.locator("text='Types'").first.click(force=True)
            page.wait_for_timeout(800)

            # 2. Выбор категории
            page.get_by_text(cat["name"]).first.click(force=True)
            page.wait_for_timeout(1500)

            # 3. Переключение на 2 mois и Tableau
            page.evaluate("""() => {
                const selects = Array.from(document.querySelectorAll('select'));
                for (const sel of selects) {
                    for (let i = 0; i < sel.options.length; i++) {
                        const opt = sel.options[i].text.toLowerCase();
                        if (opt.includes('2 mois') || opt.includes('2 months')) {
                            sel.selectedIndex = i;
                            sel.dispatchEvent(new Event('change', { bubbles: true }));
                            sel.dispatchEvent(new Event('input', { bubbles: true }));
                        }
                        if (opt.includes('tableau') || opt.includes('table')) {
                            sel.selectedIndex = i;
                            sel.dispatchEvent(new Event('change', { bubbles: true }));
                            sel.dispatchEvent(new Event('input', { bubbles: true }));
                        }
                    }
                }
            }""")
            page.wait_for_timeout(3500)

            # Раскрытие всех данных при наличии ограничения
            try:
                page.locator("button, a").filter(has_text=re.compile(r"Afficher tout", re.I)).first.click(force=True, timeout=2000)
                page.wait_for_timeout(1000)
            except Exception:
                pass

            # 4. Сбор первой строки с замерами
            for _ in range(25):
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
                        if "TA-" in h or "TB-" in h or cat["tag"] in h:
                            m = re.search(r"(T[AB]-[A-Za-z0-9\-]+)", h)
                            s_name = m.group(1) if m else h.split()[0].strip()
                            v = clean_num(v_str)
                            if not np.isnan(v):
                                val_map[s_name] = v

                    if len(val_map) > 0:
                        break

                page.wait_for_timeout(800)

        except Exception:
            pass
        finally:
            browser.close()

    return {"values": val_map, "date": latest_date_str}

def position(name):
    m_ch = re.search(r"CS(\d+)|S(\d+)", name)
    ch = float(m_ch.group(1) or m_ch.group(2)) * 10.0 if m_ch else 0.0
    ang = 0.0
    if "-L" in name:
        ang = 90.0
    elif "-R" in name:
        ang = 270.0
    elif "-T" in name or "-C" in name:
        ang = 0.0
    elif "-B" in name:
        ang = 180.0
    return np.array([ch, ang], dtype=np.float32)

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

# --- ИСХОДНЫЙ ИНТЕРФЕЙС ---
if "reload_counter" not in st.session_state:
    st.session_state.reload_counter = 0

col_ctrl, col_btn = st.columns([4, 1])
with col_ctrl:
    selected_comp = st.selectbox(
        "Layer",
        options=list(CATEGORIES.keys()),
        format_func=lambda k: CATEGORIES[k]["name"]
    )
with col_btn:
    st.write("")
    if st.button("Verileri Yenile", use_container_width=True):
        st.session_state.reload_counter += 1

cur_layer = fetch_category_data(selected_comp, reload_seed=st.session_state.reload_counter)
v_map = cur_layer.get("values", {})
latest_date = cur_layer.get("date", "")

col_3d, col_info = st.columns([3, 1])

with col_info:
    st.write(f"**Son Ölçüm Zamanı:** {latest_date if latest_date else 'Bilinmiyor'}")
    st.write(f"**Aktif Sensör Sayısı:** {len(v_map)}")
    if v_map:
        st.dataframe([{"Sensör": k, f"Değer ({CATEGORIES[selected_comp]['unit']})": v} for k, v in v_map.items()], height=500)

with col_3d:
    if not v_map:
        st.warning("⚠️ LoggIS sisteminden güncel veri alınamadı. Lütfen 'Verileri Yenile' butonunu deneyiniz.")
    else:
        names = list(v_map.keys())
        measured_values = np.array([v_map[n] for n in names])

        chainage_pts = np.linspace(0, 100, 30)
        angle_pts = np.linspace(0, 360, 30)
        patches = [{"chainage": chainage_pts, "angles": angle_pts}]

        pos, W = build_operator(names, patches)
        interpolated = W @ measured_values

        C_grid, A_grid = np.meshgrid(chainage_pts, np.radians(angle_pts))
        radius = 4.0
        X = C_grid
        Y = radius * np.cos(A_grid)
        Z = radius * np.sin(A_grid)
        I_grid = interpolated.reshape(len(angle_pts), len(chainage_pts))

        fig = go.Figure(data=[go.Surface(
            x=X, y=Y, z=Z,
            surfacecolor=I_grid,
            colorscale=CATEGORIES[selected_comp]["color_scale"],
            colorbar=dict(title=f"{CATEGORIES[selected_comp]['name']} ({CATEGORIES[selected_comp]['unit']})")
        )])

        fig.update_layout(
            scene=dict(
                xaxis_title="Chainage (m)",
                yaxis_title="Y (m)",
                zaxis_title="Z (m)",
                aspectmode="data"
            ),
            margin=dict(l=0, r=0, b=0, t=10),
            height=700
        )
        st.plotly_chart(fig, use_container_width=True)
