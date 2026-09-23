import os
import re
import sys
import base64
import subprocess
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from scipy.interpolate import RBFInterpolator
from playwright.sync_api import sync_playwright

# --- КОНФИГУРАЦИЯ СТРАНИЦЫ STREAMLIT ---
st.set_page_config(
    page_title="LOGGIS 3B Tünel İzleme Paneli",
    layout="wide",
    initial_sidebar_state="expanded"
)

URL = "https://loggis2.com/?company-id=20ce6d9f-398b-43b3-a452-3580dae39122&project-id=2d381d12-d966-4c90-a7c8-c90d6f758ae0&token-id=6e73d15f-0b2f-4d93-a152-3464f7450e50"

CATEGORIES = {
    "temperature": {"name": "Temperature", "tag": "-TP", "unit": "°C", "color_scale": "Turbo"},
    "longitudinal": {"name": "Longitudinal strains", "tag": "-L", "unit": "µε", "color_scale": "RdBu_r"},
    "othoradial": {"name": "Othoradial strains", "tag": "-CS", "unit": "µε", "color_scale": "Viridis"},
}

angle_scale = 1.0

# --- СЛУЖЕБНЫЕ ФУНКЦИИ ---
def clean_num(s):
    if not s:
        return np.nan
    try:
        s_clean = s.strip().replace(" ", "").replace(",", ".")
        return float(re.findall(r"[-+]?\d*\.?\d+", s_clean)[0])
    except Exception:
        return np.nan

def ensure_playwright_installed():
    """Автоматическая доустановка браузера Chromium на сервере Streamlit Cloud."""
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    except Exception as e:
        st.sidebar.error(f"Chromium kurulum hatası: {e}")

# --- ФУНКЦИЯ СБОРА ДАННЫХ ИЗ LOGGIS ---
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
            page.wait_for_timeout(3500)

            # 1. Открываем вкладку Types
            page.locator("text='Types'").first.click(force=True)
            page.wait_for_timeout(1000)

            # 2. Выбираем категорию сенсоров
            page.get_by_text(cat["name"]).first.click(force=True)
            page.wait_for_timeout(2000)

            # 3. ПЕРЕКЛЮЧАЕМ СЕЛЕКТОРЫ: Durée -> 2 mois, Affichage -> Tableau
            page.evaluate("""() => {
                const selects = Array.from(document.querySelectorAll('select'));
                for (const sel of selects) {
                    for (let i = 0; i < sel.options.length; i++) {
                        const optText = sel.options[i].text.toLowerCase();
                        // Выбираем 2 mois
                        if (optText.includes('2 mois') || optText.includes('2 months')) {
                            sel.selectedIndex = i;
                            sel.dispatchEvent(new Event('change', { bubbles: true }));
                            sel.dispatchEvent(new Event('input', { bubbles: true }));
                        }
                        // Выбираем Tableau
                        if (optText.includes('tableau') || optText.includes('table')) {
                            sel.selectedIndex = i;
                            sel.dispatchEvent(new Event('change', { bubbles: true }));
                            sel.dispatchEvent(new Event('input', { bubbles: true }));
                        }
                    }
                }
            }""")
            
            # Ждем 3 секунды, пока Blazor отрисует таблицу вместо графика
            page.wait_for_timeout(3500)

            # Кнопка 'Afficher tout', если замеры ограничены лимитом ячеек
            try:
                page.locator("button, a").filter(has_text=re.compile(r"Afficher tout", re.I)).first.click(force=True, timeout=2000)
                page.wait_for_timeout(1000)
            except Exception:
                pass

            # Сохраняем скриншот для визуального подтверждения
            try:
                img_bytes = page.screenshot()
                screenshot_b64 = base64.b64encode(img_bytes).decode("utf-8")
            except Exception:
                pass

            # 4. Считываем данные из появившейся таблицы
            for _ in range(25):
                extracted = page.evaluate("""(tag) => {
                    const table = document.querySelector('table');
                    if (!table) return null;

                    // Заголовки (имена датчиков)
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

                    // Самая первая строка с данными (свежая дата и значения)
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

                    if len(val_map) > 0:
                        break

                page.wait_for_timeout(800)

            if not val_map:
                debug_msg = "Селекторы переключены, но таблица не успела отрендериться."

        except Exception as e_main:
            debug_msg = f"Ошибка: {e_main}"
        finally:
            browser.close()

    return {
        "values": val_map,
        "date": latest_date_str,
        "screenshot": screenshot_b64,
        "debug": debug_msg
    }

# --- ГЕОМЕТРИЯ И ИНТЕРПОЛЯЦИЯ RBF ---
def position(name):
    # Координаты датчиков: [chainage, angle]
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
    wrapped = np.vstack([
        np.column_stack([pos[:, 0], pos[:, 1] - 360.0]),
        pos,
        np.column_stack([pos[:, 0], pos[:, 1] + 360.0]),
    ])
    wrapped[:, 1] *= angle_scale
    
    # Исправлена скобка query.shape[0]
    W = np.empty((query.shape[0], len(names)), dtype=np.float32)
    for j in range(len(names)):
        e = np.zeros(len(names))
        e[j] = 1.0
        rbf = RBFInterpolator(wrapped, np.concatenate([e, e, e]), kernel="thin_plate_spline", smoothing=1.0)
        W[:, j] = rbf(query)
    return pos, W

# --- ИНТЕРФЕЙС STREAMLIT ---
if "reload_counter" not in st.session_state:
    st.session_state.reload_counter = 0

st.sidebar.title("Parametreler")
selected_comp = st.sidebar.selectbox(
    "Ölçüm Türü (Layer)",
    options=list(CATEGORIES.keys()),
    format_func=lambda k: CATEGORIES[k]["name"]
)

if st.sidebar.button("🔄 Verileri Yenile", use_container_width=True):
    st.session_state.reload_counter += 1

st.title("🚇 LOGGIS 3B Tünel İzleme ve RBF İnterpolasyonu")

# Получение данных
with st.spinner("LoggIS portalından en güncel ölçüm değerleri alınıyor..."):
    cur_layer = fetch_category_data(selected_comp, reload_seed=st.session_state.reload_counter)

v_map = cur_layer.get("values", {})
latest_date = cur_layer.get("date", "")

col_3d, col_info = st.columns([3, 1])

with col_info:
    st.subheader("Ölçüm Özeti")
    st.metric("Son Ölçüm Zamanı", latest_date if latest_date else "Bilinmiyor")
    st.metric("Aktif Sensör Sayısı", len(v_map))
    if v_map:
        st.write("**Sensör Değerleri:**")
        st.dataframe([{"Sensör": k, f"Değer ({CATEGORIES[selected_comp]['unit']})": v} for k, v in v_map.items()], height=400)

with col_3d:
    if not v_map:
        st.error("⚠️ LoggIS sisteminden güncel veri alınamadı.")
        if cur_layer.get("debug"):
            st.code(cur_layer["debug"])
        if cur_layer.get("screenshot"):
            st.write("📸 **Tarayıcının son ekran görüntüsü:**")
            st.image(f"data:image/png;base64,{cur_layer['screenshot']}", use_container_width=True)
    else:
        # Построение 3D тоннеля с интерполяцией
        names = list(v_map.keys())
        measured_values = np.array([v_map[n] for n in names])

        # Сетка тоннеля
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
            margin=dict(l=0, r=0, b=0, t=30),
            height=650
        )
        st.plotly_chart(fig, use_container_width=True)
