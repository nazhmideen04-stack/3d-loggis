import os
import re
import sys
import csv
import json
import base64
import subprocess
from datetime import datetime
import numpy as np
import pandas as pd
import streamlit as st
from playwright.sync_api import sync_playwright

# 1. ФИРМЕННАЯ ТЕМА STREAMLIT
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

# Фирменный стиль DESTECH с мобильной адаптацией
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

    /* Радиокнопки */
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

    div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) div:first-child {
        transform: scale(1.2) !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) div:first-child div {
        background-color: #00C8E6 !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] > label {
        margin-bottom: 12px !important;
        cursor: pointer !important;
        display: flex !important;
        align-items: center !important;
    }

    div[data-baseweb="select"] {
        background-color: #0E182A !important;
        border: 1px solid rgba(0, 200, 230, 0.4) !important;
        border-radius: 6px !important;
    }

    /* Слайдер и чекбоксы */
    div[data-testid="stSlider"] div[role="slider"] {
        background-color: #00C8E6 !important;
        border-color: #00C8E6 !important;
        box-shadow: 0 0 14px #00C8E6 !important;
    }

    div[data-testid="stCheckbox"] label:has(input:checked) span[data-baseweb="checkbox"] {
        background-color: #00C8E6 !important;
        border-color: #00C8E6 !important;
    }

    div[data-testid="stCheckbox"] label span[data-baseweb="checkbox"] {
        border-color: #00C8E6 !important;
    }

    div[data-testid="stCheckbox"] svg path {
        fill: #0A0E17 !important;
        stroke: #0A0E17 !important;
    }

    .destech-badge {
        font-family: 'Syne', sans-serif;
        font-size: 15px;
        font-weight: 800;
        letter-spacing: 2px;
        background: #00C8E6;
        color: #000000;
        padding: 5px 14px;
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
        width: 100% !important;
        transition: background-color 0.2s ease, border-color 0.2s ease !important;
    }

    div.stButton > button:hover {
        background-color: #132E4C !important;
        border-color: #00C8E6 !important;
        color: #FFFFFF !important;
    }

    /* Стили для таблицы */
    [data-testid="stDataFrame"] {
        background-color: #0E182A !important;
        border-radius: 8px !important;
        padding: 10px !important;
        border: 1px solid rgba(0, 200, 230, 0.3) !important;
    }
    
    [data-testid="stDataFrame"] table th {
        color: #00C8E6 !important;
        font-family: 'Syne', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: 1px !important;
        background-color: #0A0E17 !important;
    }

    /* МОБИЛЬНАЯ АДАПТАЦИЯ - УЛУЧШЕННАЯ */
    @media (max-width: 820px) {
        .main .block-container {
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            padding-top: 1.5rem !important;
            padding-bottom: 2.5rem !important;
        }

        [data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: column-reverse !important;
            gap: 1.5rem !important;
        }

        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }

        h1, h2, h3 {
            letter-spacing: 1px !important;
        }
        h2 { font-size: 1.15rem !important; }
        h3 { font-size: 1.05rem !important; }

        .header-box h1 {
            font-size: 19px !important;
            margin-bottom: 2px !important;
        }

        .header-box div {
            font-size: 11px !important;
            letter-spacing: 1px !important;
        }

        .header-box img {
            width: 110px !important;
        }
        
        div[data-testid="stRadio"] div[role="radiogroup"] label p {
            font-size: 15px !important;
        }
        
        [data-testid="stMetricValue"] {
            font-size: 24px !important;
        }
        [data-testid="stMetricLabel"] {
            font-size: 11px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

LOGO_B64 = ""
if os.path.exists(LOGO_PATH):
    with open(LOGO_PATH, "rb") as f:
        LOGO_B64 = base64.b64encode(f.read()).decode()

LOGO_TAG = f'<img src="data:image/jpeg;base64,{LOGO_B64}" style="width: 250px; height: auto; display: block; opacity: 0.85; border-radius: 4px;" alt="DESTECH">' if LOGO_B64 else '<span class="destech-badge">DESTECH</span>'

st.markdown(f"""
<div class="header-box" style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-top: -20px; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid rgba(0, 200, 230, 0.15);">
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
    "hoop": {"names": ["Othoradial Strains", "Orthoradial Strains", "Orthoradial"], "tag": "-CS", "title": "Çevresel gerinim (CS)", "unit": "µm/m"},
    "axial": {"names": ["Longitudinal Strains", "Longitudinal"], "tag": "-S", "title": "Boyuna gerinim (S)", "unit": "µm/m"},
    "temp": {"names": ["Temperature", "Temperatures", "Température", "Températures"], "tag": "-TP", "title": "Sıcaklık (TP)", "unit": "°C"},
}

SENSOR_RE = re.compile(r"(?<![A-Za-z0-9])(T[AB]-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)", re.IGNORECASE)

TR_MONTHS = {
    "01": "Ocak", "02": "Şubat", "03": "Mart", "04": "Nisan", "05": "Mayıs", "06": "Haziran",
    "07": "Temmuz", "08": "Ağustos", "09": "Eylül", "10": "Ekim", "11": "Kasım", "12": "Aralık",
}

DATE_FORMATS = [
    "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y",
    "%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M", "%d.%m.%Y",
    "%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M", "%d-%m-%Y",
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
    "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M", "%Y/%m/%d",
    "%d/%m/%y %H:%M:%S", "%d/%m/%y %H:%M",
]

def clean_num(s):
    if s is None:
        return np.nan
    if isinstance(s, (int, float, np.integer, np.floating)):
        return float(s)
    s = str(s).strip()
    if not s:
        return np.nan
    s = s.replace("\u2212", "-").replace("\u2013", "-")
    s = re.sub(r"[\s\u00a0\u202f\u2009']", "", s)
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    else:
        s = s.replace(",", ".")
    m = re.search(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", s)
    return float(m.group()) if m else np.nan

def parse_ts(s):
    if s is None:
        return None
    t = str(s).replace("\ufeff", "").strip()
    if not t or not re.search(r"\d", t):
        return None
    t = re.sub(r"\s+", " ", t.replace("T", " "))
    t = re.sub(r"(\.\d+)?(Z|[+-]\d{2}:?\d{2})$", "", t).strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(t, fmt)
        except ValueError:
            pass
    if not re.search(r"\d{1,4}[./-]\d{1,2}[./-]\d{1,4}", t):
        return None
    try:
        ts = pd.to_datetime(t, dayfirst=True, errors="coerce")
        if pd.notna(ts):
            return ts.to_pydatetime().replace(tzinfo=None)
    except Exception:
        pass
    return None

def ts_key(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def fmt_ts(key):
    if not key or key == "-":
        return "-"
    try:
        return datetime.strptime(key, "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y %H:%M")
    except ValueError:
        return str(key)

SENSOR_RE_ALT = re.compile(r"(?<![A-Za-z0-9])([A-Za-z0-9]+(?:-[A-Za-z0-9]+)*-(?:CS|S|TP)\d[A-Za-z0-9]*(?:-[A-Za-z0-9]+)*)")

def extract_sensor_name(header):
    if header is None:
        return None
    h = str(header).replace("\ufeff", "")
    m = SENSOR_RE.search(h) or SENSOR_RE_ALT.search(h)
    return m.group(1).strip("-") if m else None

def classify_sensor(name):
    if not name:
        return None
    segs = name.upper().split("-")[1:]
    if any(s.startswith("CS") for s in segs):
        return "hoop"
    if any(s.startswith("S") for s in segs):
        return "axial"
    if any(s.startswith("TP") for s in segs):
        return "temp"
    return None

def ensure_playwright_installed():
    try: subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    except Exception: pass

BROWSER_ARGS = [
    "--no-sandbox", "--disable-setuid-sandbox",
    "--disable-dev-shm-usage", "--disable-gpu", "--window-size=1920,1080"
]

def _launch_browser(p):
    try:
        return p.chromium.launch(headless=True, args=BROWSER_ARGS)
    except Exception:
        ensure_playwright_installed()
        return p.chromium.launch(headless=True, args=BROWSER_ARGS)

def _new_page(browser):
    context = browser.new_context(
        accept_downloads=True, viewport={"width": 1920, "height": 1080},
        timezone_id="Europe/Istanbul", locale="fr-FR",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36"
    )
    return context.new_page()

def _select_combo(page, index, value, log, label):
    try:
        page.wait_for_selector(f'select option[value="{value}"]', state="attached", timeout=30000)
    except Exception:
        pass
    try:
        page.get_by_role("combobox").nth(index).select_option(value, timeout=15000)
        return True
    except Exception:
        pass
    try:
        page.locator(f'select:has(option[value="{value}"])').first.select_option(value, timeout=10000)
        return True
    except Exception as e:
        log.append(f"{label}='{value}' seçilemedi ({type(e).__name__})")
        return False

def _click_types(page, log):
    for kwargs in ({}, {"force": True}):
        try:
            page.get_by_text("Types", exact=True).first.click(timeout=10000, **kwargs)
            break
        except Exception:
            continue
    else:
        log.append("'Types' tıklanamadı")
    try:
        page.get_by_role("listbox").first.wait_for(state="attached", timeout=15000)
    except Exception:
        log.append("Kategori listesi (listbox) bulunamadı")

def _open_loggis(page, mode_type, view_type=None, log=None):
    log = log if log is not None else []
    page.goto(URL, timeout=90000, wait_until="domcontentloaded")
    try: page.wait_for_load_state("networkidle", timeout=30000)
    except Exception: pass
    page.wait_for_timeout(2000)
    _select_combo(page, 0, mode_type, log, "Durée")
    page.wait_for_timeout(1500)
    if view_type:
        _select_combo(page, 1, view_type, log, "Affichage")
        page.wait_for_timeout(1500)
    _click_types(page, log)
    page.wait_for_timeout(1000)
    return log

def _select_category(page, cat_cfg, log=None):
    lb = page.get_by_role("listbox").first
    for c_name in cat_cfg["names"]:
        try:
            lb.select_option(c_name, timeout=3000)
            return True
        except Exception: pass
    for c_name in cat_cfg["names"]:
        try:
            lb.select_option(label=c_name, timeout=2000)
            return True
        except Exception: pass
    try:
        opts = lb.locator("option").all_inner_texts()
        for c_name in cat_cfg["names"]:
            for o in opts:
                if c_name.lower() in o.lower():
                    lb.select_option(label=o, timeout=2000)
                    return True
        if log is not None:
            log.append(f"Kategori bulunamadı: {cat_cfg['names'][0]} (mevcut: {', '.join(o.strip() for o in opts[:8])})")
    except Exception:
        if log is not None:
            log.append(f"Kategori seçilemedi: {cat_cfg['names'][0]}")
    return False

_TABLE_JS = r"""
() => {
  const txt = el => (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim();
  const expand = cells => {
    const out = [];
    cells.forEach(c => {
      const n = parseInt(c.getAttribute('colspan') || '1', 10) || 1;
      const t = txt(c);
      for (let i = 0; i < n; i++) out.push(t);
    });
    return out;
  };
  const result = [];
  document.querySelectorAll('table').forEach(t => {
    const headRows = [], bodyRows = [];
    t.querySelectorAll('tr').forEach(tr => {
      if (tr.closest('table') !== t) return;
      const cells = Array.from(tr.children).filter(c => c.tagName === 'TH' || c.tagName === 'TD');
      if (!cells.length) return;
      const inHead = !!tr.closest('thead') || cells.every(c => c.tagName === 'TH');
      (inHead ? headRows : bodyRows).push(expand(cells));
    });
    result.push({ headRows, bodyRows });
  });
  document.querySelectorAll('[role="grid"],[role="table"],[role="treegrid"]').forEach(g => {
    if (g.tagName === 'TABLE') return;
    const headRows = [], bodyRows = [];
    g.querySelectorAll('[role="row"]').forEach(r => {
      const hc = Array.from(r.querySelectorAll('[role="columnheader"]'));
      const bc = Array.from(r.querySelectorAll('[role="gridcell"],[role="cell"],[role="rowheader"]'));
      if (hc.length && !bc.length) headRows.push(hc.map(txt));
      else if (bc.length) bodyRows.push(bc.map(txt));
    });
    result.push({ headRows, bodyRows });
  });
  return result;
}
"""

_SCROLL_JS = r"""
() => {
  document.querySelectorAll('*').forEach(el => {
    if (el.scrollHeight > el.clientHeight + 20 && el.querySelector('table,[role="row"]')) {
      el.scrollTop = el.scrollHeight;
    }
  });
  window.scrollTo(0, document.body.scrollHeight);
}
"""

def _pick_sensor_table(raw_tables):
    best = None
    for tbl in raw_tables or []:
        head_rows = list(tbl.get("headRows") or [])
        body_rows = list(tbl.get("bodyRows") or [])
        candidates = [(h, body_rows) for h in head_rows]
        if not head_rows and body_rows:
            candidates.append((body_rows[0], body_rows[1:]))
        for header, rows in candidates:
            cols = [(j, extract_sensor_name(h)) for j, h in enumerate(header)]
            cols = [(j, n) for j, n in cols if n]
            if cols and (best is None or len(cols) > len(best["cols"])):
                best = {"header": header, "cols": cols, "rows": rows}
    return best

def _last_row_values(tbl):
    header_len = len(tbl["header"])
    rows = []
    for idx, row in enumerate(tbl["rows"]):
        offset = len(row) - header_len if len(row) > header_len else 0
        vals = {}
        for j, name in tbl["cols"]:
            k = j + offset
            if k < len(row):
                v = clean_num(row[k])
                if not np.isnan(v):
                    vals[name] = v
        if not vals:
            continue
        dt = None
        for cell in row[:3]:
            dt = parse_ts(cell)
            if dt: break
        rows.append((idx, dt, vals))
    if not rows:
        return None, {}, {}

    dated = [r for r in rows if r[1]]
    if dated:
        ordered = sorted(dated, key=lambda r: (r[1], r[0]), reverse=True)
    else:
        ordered = sorted(rows, key=lambda r: r[0], reverse=True)

    latest_dt = ordered[0][1]
    vals, times = {}, {}
    for _, dt, row_vals in ordered:
        for name, v in row_vals.items():
            if name not in vals:
                vals[name] = v
                times[name] = ts_key(dt) if dt else None
    return latest_dt, vals, times

def _wait_data_loaded(page, timeout=30000):
    try:
        page.wait_for_function(
            """() => !Array.from(document.querySelectorAll('body *')).some(e =>
                   e.children.length === 0 && e.offsetParent !== null &&
                   /Récupération des données/i.test(e.textContent || ''))""",
            timeout=timeout)
    except Exception:
        pass
    page.wait_for_timeout(1000)

def _download_csv(page, log=None, tag=""):
    ctx = page.context
    downloads = []
    on_download = lambda d: downloads.append(d)
    def on_page(new_page):
        try: new_page.on("download", on_download)
        except Exception: pass
    page.on("download", on_download)
    ctx.on("page", on_page)
    pages_before = set(ctx.pages)

    btn = page.get_by_text("🠋CSV").first
    try:
        btn.wait_for(state="attached", timeout=20000)
    except Exception:
        btn = page.locator("text=CSV").first
        if btn.count() == 0:
            if log is not None:
                log.append("'🠋CSV' düğmesi bulunamadı")
            return None

    path = None
    try:
        for attempt, wait_steps in enumerate((90, 30)):
            try:
                btn.click(timeout=10000)
            except Exception:
                try: btn.click(force=True, timeout=5000)
                except Exception:
                    try: btn.dispatch_event("click")
                    except Exception: pass
            for _ in range(wait_steps):
                if downloads: break
                page.wait_for_timeout(500)
            if downloads: break
        if downloads:
            path = downloads[-1].path()
        elif log is not None:
            log.append(f"CSV indirilemedi {tag}".strip())
    except Exception as e:
        if log is not None:
            log.append(f"CSV hatası {tag}: {type(e).__name__}".strip())
    finally:
        try: page.remove_listener("download", on_download)
        except Exception: pass
        try: ctx.remove_listener("page", on_page)
        except Exception: pass
        for pg in list(ctx.pages):
            if pg is not page and pg not in pages_before:
                try: pg.close()
                except Exception: pass
    return path if path and os.path.exists(path) else None

@st.cache_data(ttl=300, show_spinner=False)
def _fetch_live_cached(mode_type):
    live_db = {k: {} for k in CATEGORIES}
    latest_key = None
    log = []

    with sync_playwright() as p:
        browser = _launch_browser(p)
        page = _new_page(browser)
        try:
            _open_loggis(page, mode_type, view_type="TABLE_ROW_DATE", log=log)
            if page.get_by_role("listbox").count() == 0:
                raise RuntimeError(" | ".join(log) or "LoggIS sayfası açılamadı")

            for cat_key, cat_cfg in CATEGORIES.items():
                if live_db[cat_key]:
                    continue
                _select_category(page, cat_cfg, log)
                page.wait_for_timeout(2000)
                _wait_data_loaded(page)
                try:
                    page.wait_for_function(
                        """() => Array.from(document.querySelectorAll('th,td,[role="columnheader"]'))
                                 .some(e => /T[AB]-/i.test(e.textContent || ''))""",
                        timeout=25000)
                except Exception: pass
                try:
                    page.evaluate(_SCROLL_JS)
                    page.wait_for_timeout(800)
                except Exception: pass

                cat_ts, vals = None, {}
                try:
                    raw = page.evaluate(_TABLE_JS)
                    tbl = _pick_sensor_table(raw)
                    if tbl:
                        dt, vals, _ = _last_row_values(tbl)
                        cat_ts = ts_key(dt) if dt else None
                    else:
                        log.append(f"Tablo ({cat_key}): {len(raw)} tablo, TA-/TB- sütunu yok")
                except Exception as e:
                    log.append(f"Tablo ({cat_key}): {type(e).__name__}")

                if not vals:
                    path = _download_csv(page, log, f"({cat_key})")
                    if path:
                        parsed, _, head = parse_loggis_csv(path)
                        cat_ts, vals = _latest_from_parsed(parsed)
                        if not vals:
                            log.append(f"CSV ({cat_key}) okunamadı, başlık: {head[:120]}")

                for s_name, v in vals.items():
                    c = classify_sensor(s_name)
                    if c:
                        live_db[c][s_name] = v
                if cat_ts and (latest_key is None or cat_ts > latest_key):
                    latest_key = cat_ts
        except RuntimeError:
            raise
        except Exception as e:
            log.append(f"{type(e).__name__}: {str(e).splitlines()[0][:150]}")
        finally:
            browser.close()

    if not any(live_db.values()):
        raise RuntimeError(" | ".join(log) or "Canlı veri alınamadı")
    return live_db, latest_key or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def fetch_live_table(mode_type="MONTH_02"):
    try:
        live_db, ts = _fetch_live_cached(mode_type)
        return live_db, {"timestamp": ts, "error": None}
    except Exception as e:
        return {k: {} for k in CATEGORIES}, {"timestamp": None, "error": str(e)}

def _read_text_any(path):
    with open(path, "rb") as f:
        raw = f.read()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16", errors="ignore")
    for enc in ("utf-8-sig", "cp1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("latin-1", errors="ignore")

def parse_loggis_csv(path):
    text = _read_text_any(path).replace("\ufeff", "")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return {}, 0, ""

    sample = "\n".join(lines[:5])
    delim = max([";", "\t"], key=sample.count)
    if sample.count(delim) == 0:
        delim = ","
    rows = list(csv.reader(lines, delimiter=delim))

    header_idx, best_cols = None, []
    for i, row in enumerate(rows[:15]):
        cols = [(j, extract_sensor_name(h)) for j, h in enumerate(row)]
        cols = [(j, n) for j, n in cols if n]
        if len(cols) > len(best_cols):
            header_idx, best_cols = i, cols
    if header_idx is None:
        return {}, 0, lines[0]

    out = {}
    for row in rows[header_idx + 1:]:
        dt = None
        for cell in row[:3]:
            dt = parse_ts(cell)
            if dt: break
        if not dt:
            continue
        vals = {}
        for j, name in best_cols:
            if j < len(row):
                v = clean_num(row[j])
                if not np.isnan(v):
                    vals[name] = v
        if vals:
            out.setdefault(ts_key(dt), {}).update(vals)
    return out, len(best_cols), lines[header_idx]

@st.cache_data(ttl=900, show_spinner=False)
def _fetch_csv_cached(mode_type):
    historical_db = {k: {} for k in CATEGORIES}
    log = []

    with sync_playwright() as p:
        browser = _launch_browser(p)
        page = _new_page(browser)
        try:
            _open_loggis(page, mode_type, log=log)
            if page.get_by_role("listbox").count() == 0:
                raise RuntimeError(" | ".join(log) or "LoggIS sayfası açılamadı")

            for cat_key, cat_cfg in CATEGORIES.items():
                _select_category(page, cat_cfg, log)
                page.wait_for_timeout(2000)
                _wait_data_loaded(page)

                path = _download_csv(page, log, f"({cat_key})")
                if not path:
                    continue
                parsed, n_cols, head = parse_loggis_csv(path)
                if not parsed:
                    log.append(f"CSV ({cat_key}) okunamadı, başlık: {head[:120]}")
                for key, vals in parsed.items():
                    for s_name, v in vals.items():
                        c = classify_sensor(s_name)
                        if c:
                            historical_db[c].setdefault(key, {})[s_name] = v
        except RuntimeError:
            raise
        except Exception as e:
            log.append(f"{type(e).__name__}: {str(e).splitlines()[0][:150]}")
        finally:
            browser.close()

    all_keys = set()
    for cat_rows in historical_db.values():
        all_keys.update(k for k, v in cat_rows.items() if v)
    if not all_keys:
        raise RuntimeError(" | ".join(log) or "CSV arşiv verisi alınamadı")
    return sorted(all_keys, reverse=True), historical_db

def fetch_csv_database(mode_type="ALL"):
    try:
        dates, db = _fetch_csv_cached(mode_type)
        return dates, db, {"error": None}
    except Exception as e:
        return [], {k: {} for k in CATEGORIES}, {"error": str(e)}

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

    diag = None
    if data_mode == "Arşiv Veriler":
        st.markdown("---")
        st.subheader("Zaman Seçimi")
        
        with st.spinner("Arşiv tarihleri yükleniyor..."):
            all_dates, full_db, diag = fetch_csv_database(mode_type="ALL")
        if diag.get("error"):
            st.warning(f"LoggIS bağlantı hatası: {diag['error']}")

        cat_rows = full_db[selected_comp]
        cat_dates = sorted([k for k, v in cat_rows.items() if v], reverse=True)
            
        if not cat_dates:
            st.warning("Arşiv verisi bulunamadı.")
        else:
            latest_key = cat_dates[0]
            latest_timestamp = fmt_ts(latest_key)
            
            compare_mode = st.checkbox("Karşılaştır (Fark Analizi)")

            date_hierarchy = {}
            for k in cat_dates:
                y, m, d, t = k[0:4], k[5:7], k[8:10], k[11:]
                date_hierarchy.setdefault(y, {}).setdefault(m, {}).setdefault(d, []).append(t)

            years = sorted(date_hierarchy.keys(), reverse=True)
            sel_year = st.selectbox("Yıl Seçiniz", options=years)

            if sel_year:
                months = sorted(date_hierarchy[sel_year].keys(), reverse=True)
                sel_month = st.selectbox("Ay Seçiniz:", options=months,
                                         format_func=lambda mm: f"{mm} - {TR_MONTHS.get(mm, mm)}")

                if sel_month:
                    days = sorted(date_hierarchy[sel_year][sel_month].keys(), reverse=True)
                    sel_day = st.selectbox("Gün Seçiniz:", options=days)

                    if sel_day:
                        times = sorted(date_hierarchy[sel_year][sel_month][sel_day], reverse=True)
                        sel_time = st.selectbox("Saat Seçiniz:", options=times, format_func=lambda t: t[:5])

                        if sel_time:
                            target_key = f"{sel_year}-{sel_month}-{sel_day} {sel_time}"
                            target_timestamp = fmt_ts(target_key)
                            raw_v_map = cat_rows.get(target_key, {})
                            latest_v_map = cat_rows.get(latest_key, {})
    else:
        with st.spinner("En güncel veriler alınıyor..."):
            live_db, diag = fetch_live_table(mode_type="MONTH_02")
        if diag.get("error"):
            st.warning(f"LoggIS bağlantı hatası: {diag['error']}")
        raw_v_map = live_db.get(selected_comp, {})
        if raw_v_map:
            target_timestamp = fmt_ts(diag.get("timestamp"))
        else:
            st.warning("Canlı tabloda bu kategori için veri bulunamadı.")

    if st.button("Verileri Yenile"):
        st.cache_data.clear()
        st.rerun()

# ---------------------------------------------------------
# ФИЛЬТРАЦИЯ И РАСЧЕТ ДЕЛЬТЫ (РАЗНИЦЫ)
# ---------------------------------------------------------
active_category_values = {}
table_data = [] 

if raw_v_map:
    for s_name, val in raw_v_map.items():
        if val is None or np.isnan(val): continue
        if classify_sensor(s_name) == selected_comp:
            if compare_mode:
                latest_val = latest_v_map.get(s_name)
                
                str_val = f"{float(val):.2f}"
                str_latest = f"{float(latest_val):.2f}" if latest_val is not None and not np.isnan(latest_val) else "-"
                
                if latest_val is not None and not np.isnan(latest_val):
                    delta = float(latest_val) - float(val)
                    active_category_values[s_name] = delta
                    str_delta = f"{delta:+.2f}"
                else:
                    str_delta = "-"
                    
                table_data.append({
                    "Sensör No": s_name,
                    "Arşiv Değeri": str_val,
                    "Güncel Değer": str_latest,
                    "Fark (Δ)": str_delta
                })
            else:
                active_category_values[s_name] = float(val)

# Расчет шкалы: Для Дельты шкала симметрична [-Max, +Max]
vals = [float(v) for v in active_category_values.values() if not np.isnan(v)]
if not vals:
    clim = [-1.0, 1.0]
else:
    if compare_mode:
        max_abs = max(abs(min(vals)), abs(max(vals)))
        if max_abs < 0.001:
            clim = [-0.5, 0.5]
        else:
            buf = max_abs * 0.05
            clim = [-round(max_abs + buf, 2), round(max_abs + buf, 2)]
    else:
        real_min = float(min(vals))
        real_max = float(max(vals))
        diff = abs(real_max - real_min)
        if diff < 0.001:
            clim = [round(real_min - 0.5, 2), round(real_max + 0.5, 2)]
        else:
            buf = diff * 0.02
            clim = [round(real_min - buf, 2), round(real_max + buf, 2)]

with col_nav:
    st.markdown("---")
    st.subheader("GÖRÜNÜM AYARLARI")

    tunnel_opacity = st.slider("Tünel Opaklığı (%):", min_value=0, max_value=100, value=85, step=5) / 100.0
    show_meters = st.checkbox("Metre Cetveli Göster", value=True)
    show_no_data_red = st.checkbox("⚠️ Verisi Olmayan Sensörleri Göster", value=False)

    st.markdown("---")
    if compare_mode:
        st.write("**Karşılaştırma (Fark Analizi):**")
        st.markdown(f"<span class='neon-data' style='font-size: 13px; color: #FF9500;'>{target_timestamp}  ➔  {latest_timestamp}</span>", unsafe_allow_html=True)
    else:
        st.write("**Aktif Periyot:**")
        st.markdown(f"<span class='neon-data' style='font-size: 13px;'>{target_timestamp if target_timestamp != '-' else '-'}</span>", unsafe_allow_html=True)
    
    st.write("**Aktif Sensör Sayısı:**")
    sensor_count_str = str(len(active_category_values)) if active_category_values else "-"
    st.markdown(f"<span class='neon-data' style='font-size: 18px;'>{sensor_count_str}</span>", unsafe_allow_html=True)
    
    st.write("**Skala Limitleri:**")
    if vals:
        limit_str = f"Min: {clim[0]:+.2f} | Maks: {clim[1]:+.2f} {cat_cfg['unit']}"
    else:
        limit_str = "-"
    st.markdown(f"<span class='neon-data' style='font-size: 14px;'>{limit_str}</span>", unsafe_allow_html=True)

# --- 3B THREE.JS ОБЛАСТЬ ---
with col_3d:
    sensor_options = ["Seçiniz..."] + sorted(list(active_category_values.keys()))
    
    sel_col1, sel_col2 = st.columns([3, 1])
    with sel_col1:
        selected_sensor = st.selectbox(
            "Modelde Sensör Odakla:", 
            options=sensor_options,
            help="Modelde vurgulanacak и kameranın odaklanacağı sensörü seçin"
        )
    with sel_col2:
        if selected_sensor != "Seçiniz..." and selected_sensor in active_category_values:
            val_label = "Değişim (Δ)" if compare_mode else "Ölçüm"
            st.metric(
                label=f"{val_label} ({selected_sensor})",
                value=f"{active_category_values[selected_sensor]:+.2f} {cat_cfg['unit']}"
            )
        else:
            st.metric(label="Değer" if compare_mode else "Ölçüm", value="-")

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
            "showNoDataRed": show_no_data_red,
            "isCompareMode": compare_mode
        }
        json_payload = json.dumps(payload_data)

        raw_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
        body { margin: 0; padding: 0; overflow: hidden; background-color: #0A0E17; font-family: 'Chakra Petch', sans-serif; touch-action: none; border-radius: 8px; }
        #canvas-container { width: 100%; height: 100vh; position: relative; }
        #sensor-tooltip { position: absolute; display: none; background: rgba(14, 24, 42, 0.95); border: 1px solid #00C8E6; color: #FFFFFF; padding: 6px 12px; border-radius: 6px; font-size: 13px; pointer-events: none; z-index: 100; box-shadow: 0 4px 16px rgba(0, 200, 230, 0.35); }
        #selected-hud { position: absolute; top: 14px; left: 14px; display: none; background: rgba(10, 14, 23, 0.92); border: 1px solid #00C8E6; padding: 8px 14px; border-radius: 8px; z-index: 95; box-shadow: 0 4px 16px rgba(0, 200, 230, 0.3); max-width: 220px; }
        #selected-hud .hud-title { font-size: 11px; color: #8397AD; text-transform: uppercase; letter-spacing: 0.8px; }
        #selected-hud .hud-name { font-size: 15px; color: #FFFFFF; font-weight: 700; margin: 1px 0 3px 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        #selected-hud .hud-val { font-size: 18px; color: #00E5FF; font-weight: 700; }
        #loader { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: #00C8E6; font-size: 16px; font-weight: 700; letter-spacing: 1px; text-align: center; width: 80%; }
        #color-legend { position: absolute; top: 14px; right: 14px; display: flex; flex-direction: column; align-items: center; background: rgba(10, 14, 23, 0.92); padding: 10px 12px; border: 1px solid rgba(0, 200, 230, 0.55); box-shadow: 0 0 16px rgba(0, 200, 230, 0.25); border-radius: 6px; z-index: 90; user-select: none; }
        #legend-title { color: #00E5FF; font-size: 12px; font-weight: 700; margin-bottom: 6px; text-transform: none !important; letter-spacing: 0.5px; }
        .legend-bar-container { display: flex; align-items: stretch; height: 180px; }
        #legend-bar { width: 16px; border-radius: 4px; border: 1px solid rgba(255, 255, 255, 0.35); margin-right: 8px; }
        .legend-labels { display: flex; flex-direction: column; justify-content: space-between; color: #FFFFFF; font-size: 11px; font-weight: 700; }
        @media (max-width: 600px) { #color-legend { padding: 6px 8px; top: 10px; right: 10px; } .legend-bar-container { height: 130px; } #legend-bar { width: 12px; } #legend-title { font-size: 10px; } .legend-labels { font-size: 9px; } #selected-hud { top: 10px; left: 10px; padding: 6px 10px; } #selected-hud .hud-name { font-size: 13px; } #selected-hud .hud-val { font-size: 15px; } }
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
            <div class="hud-title">Seçilen Sensör</div>
            <div id="hud-sensor-name" class="hud-name">--</div>
            <div id="hud-sensor-val" class="hud-val">-</div>
        </div>
        <div id="color-legend">
            <div id="legend-title"></div>
            <div class="legend-bar-container">
                <div id="legend-bar"></div>
                <div class="legend-labels">
                    <span id="lbl-max">-</span>
                    <span id="lbl-mid">-</span>
                    <span id="lbl-min">-</span>
                </div>
            </div>
        </div>
    </div>

    <script>
        const payload = __INJECT_PAYLOAD__;
        const modelB64 = "__INJECT_MODEL__";
        
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

        // =========================================================================
        // СИСТЕМА СОХРАНЕНИЯ ПОЛОЖЕНИЯ КАМЕРЫ
        // =========================================================================
        let isModelLoaded = false;
        
        function saveCamState() {
            if (!isModelLoaded) return;
            try {
                window.sessionStorage.setItem('loggis_cam_v7', JSON.stringify({
                    pos: camera.position.toArray(),
                    tgt: controls.target.toArray()
                }));
            } catch(e) {}
        }

        // =========================================================================
        // ЦВЕТОВЫЕ ШКАЛЫ
        // =========================================================================

        const hoopStops = [
            new THREE.Color("#050833"), new THREE.Color("#0044FF"), new THREE.Color("#00D5FF"),
            new THREE.Color("#00FF66"), new THREE.Color("#FFEE00"), new THREE.Color("#FF7700"), new THREE.Color("#FF0022")
        ];
        const axialStops = [
            new THREE.Color("#080038"), new THREE.Color("#2A0A5E"), new THREE.Color("#630F78"),
            new THREE.Color("#9E1B7F"), new THREE.Color("#D32B6E"), new THREE.Color("#F55447"), new THREE.Color("#FF9500") 
        ];
        const temperatureStops = [
            new THREE.Color("#020024"), new THREE.Color("#0033FF"), new THREE.Color("#00D8FF"),
            new THREE.Color("#00FF44"), new THREE.Color("#B4FF00"), new THREE.Color("#FFDD00"),
            new THREE.Color("#FF4400"), new THREE.Color("#D50000")
        ];

        const compareStops = [
            new THREE.Color("#0055FF"), 
            new THREE.Color("#00E5FF"), 
            new THREE.Color("#2E3A59"), 
            new THREE.Color("#FFDD00"), 
            new THREE.Color("#FF0033")  
        ];

        let currentStops = hoopStops;
        if (payload.isCompareMode) {
            currentStops = compareStops;
            legendTitle.innerText = "Δ Fark [" + payload.unit + "]";
        } else {
            if (payload.comp === "axial") { currentStops = axialStops; legendTitle.innerText = "Boyuna [" + payload.unit + "]"; }
            else if (payload.comp === "temp") { currentStops = temperatureStops; legendTitle.innerText = "Sıcaklık [" + payload.unit + "]"; }
            else { currentStops = hoopStops; legendTitle.innerText = "Çevresel [" + payload.unit + "]"; }
        }

        const labelPrefix = payload.isCompareMode ? "Fark (Δ): " : "Ölçüm: ";

        function buildExactLegendGradient(stops) {
            const n = stops.length; const items = [];
            for (let i = 0; i < n; i++) {
                const colorObj = stops[n - 1 - i];
                items.push('#' + colorObj.getHexString() + ' ' + ((i / (n - 1)) * 100).toFixed(1) + '%');
            }
            return 'linear-gradient(to bottom, ' + items.join(', ') + ')';
        }
        legendBar.style.background = buildExactLegendGradient(currentStops);

        function sampleColorRamp(stops, t) {
            t = Math.max(0.0, Math.min(1.0, t));
            const scaled = t * (stops.length - 1);
            const idx = Math.floor(scaled); const fract = scaled - idx;
            if (idx >= stops.length - 1) return stops[stops.length - 1].clone();
            const c = new THREE.Color(); c.lerpColors(stops[idx], stops[idx + 1], fract);
            return c;
        }

        function getColorForValue(val, clim) {
            if (val === undefined || isNaN(val)) return new THREE.Color(0x08111e);
            const min = clim[0], max = clim[1]; let t = (val - min) / ((max - min) || 1.0);
            return sampleColorRamp(currentStops, t);
        }

        const finalMin = payload.clim[0]; const finalMax = payload.clim[1]; const finalMid = (finalMin + finalMax) / 2.0;
        lblMax.innerText = (finalMax !== undefined && !isNaN(finalMax)) ? ((finalMax > 0 ? "+" : "") + finalMax.toFixed(2)) : "-";
        lblMid.innerText = (finalMid !== undefined && !isNaN(finalMid)) ? ((finalMid > 0 ? "+" : "") + finalMid.toFixed(2)) : "-";
        lblMin.innerText = (finalMin !== undefined && !isNaN(finalMin)) ? ((finalMin > 0 ? "+" : "") + finalMin.toFixed(2)) : "-";

        const scene = new THREE.Scene(); scene.background = new THREE.Color(0x0A0E17);
        const sensorScene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 5000);

        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.autoClear = false; container.appendChild(renderer.domElement);

        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true; controls.dampingFactor = 0.05;
        controls.minDistance = 0.5; controls.maxDistance = 2500;
        controls.touches = { ONE: THREE.TOUCH.ROTATE, TWO: THREE.TOUCH.DOLLY_PAN };

        controls.addEventListener('change', saveCamState);

        const ambientLight = new THREE.AmbientLight(0xffffff, 1.4); scene.add(ambientLight);
        const dirLight1 = new THREE.DirectionalLight(0x00E5FF, 1.6); dirLight1.position.set(60, 100, 80); scene.add(dirLight1);
        const dirLight2 = new THREE.DirectionalLight(0xffffff, 1.0); dirLight2.position.set(-60, -40, -80); scene.add(dirLight2);

        const interactiveSensors = []; const tunnelMeshes = [];
        const raycaster = new THREE.Raycaster(); raycaster.params.Line = { threshold: 1.5 }; raycaster.params.Points = { threshold: 1.5 };
        const mouse = new THREE.Vector2();

        function extractSensorId(name) { const m = name.match(/T[AB]-[A-Za-z0-9\-]+/i); return m ? m[0] : name; }
        function normalizeKey(str) { return String(str).toUpperCase().replace(/[^A-Z0-9]/g, ''); }
        function getCanonicalSensorId(name) {
            const m = name.match(/(T[AB])-([A-Za-z]+)0*(\d+)-([A-Za-z0-9]+)/i);
            if (m) return (m[1] + '-' + m[2] + parseInt(m[3], 10) + '-' + m[4]).toUpperCase();
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
            const uId = sensorId.toUpperCase(), nId = normalizeKey(sensorId), cId = getCanonicalSensorId(sensorId);
            if (normalizedDataMap[uId]) return { found: true, key: normalizedDataMap[uId].canonicalKey, val: normalizedDataMap[uId].val };
            if (normalizedDataMap[cId]) return { found: true, key: normalizedDataMap[cId].canonicalKey, val: normalizedDataMap[cId].val };
            if (normalizedDataMap[nId]) return { found: true, key: normalizedDataMap[nId].canonicalKey, val: normalizedDataMap[nId].val };
            return { found: false, key: sensorId, val: NaN };
        }

        function createPortalMarker(text) {
            const canvas = document.createElement('canvas'); canvas.width = 2048; canvas.height = 1024; const ctx = canvas.getContext('2d');
            ctx.fillStyle = 'rgba(10, 14, 23, 0.95)'; ctx.strokeStyle = '#00C8E6'; ctx.lineWidth = 56;
            ctx.strokeRect(40, 40, 1968, 944); ctx.fillRect(40, 40, 1968, 944);
            ctx.font = '900 540px Syne, Chakra Petch, sans-serif'; ctx.fillStyle = '#00E5FF'; ctx.shadowColor = '#00C8E6'; ctx.shadowBlur = 72;
            ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(text, 1024, 512);
            const texture = new THREE.CanvasTexture(canvas); const mat = new THREE.SpriteMaterial({ map: texture, depthTest: false });
            const sprite = new THREE.Sprite(mat); sprite.scale.set(24.0, 12.0, 1); return sprite;
        }

        function createRulerLabel(text) {
            const canvas = document.createElement('canvas'); canvas.width = 256; canvas.height = 128; const ctx = canvas.getContext('2d');
            ctx.fillStyle = 'rgba(10, 14, 23, 0.9)'; ctx.strokeStyle = 'rgba(0, 229, 255, 0.85)'; ctx.lineWidth = 5;
            ctx.strokeRect(6, 6, 244, 116); ctx.fillRect(6, 6, 244, 116);
            ctx.font = '700 48px Chakra Petch, sans-serif'; ctx.fillStyle = '#FFFFFF'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(text, 128, 64);
            const texture = new THREE.CanvasTexture(canvas); const mat = new THREE.SpriteMaterial({ map: texture, depthTest: false });
            const sprite = new THREE.Sprite(mat); sprite.scale.set(2.4, 1.2, 1); return sprite;
        }

        const binaryStr = atob(modelB64); const bytes = new Uint8Array(binaryStr.length);
        for (let i = 0; i < binaryStr.length; i++) bytes[i] = binaryStr.charCodeAt(i);
        let selectedMeshRef = null;

        const gltfLoader = new THREE.GLTFLoader();
        gltfLoader.parse(bytes.buffer, '', function(gltf) {
            const model = gltf.scene; scene.add(model); model.updateMatrixWorld(true); loaderText.style.display = 'none';

            const rawSensors = [];
            model.traverse(function(child) {
                if (child.isLine || child.isLineSegments) { child.visible = false; return; }
                if (child.isMesh) {
                    const name = child.name; const uName = name.toUpperCase();
                    if (uName.includes("BOX001")) { child.visible = false; return; }

                    const isSensorObject = (uName.startsWith("TA-") || uName.startsWith("TB-") || uName.includes("-CS") || uName.includes("-S") || uName.includes("-TP"));
                    if (isSensorObject) {
                        rawSensors.push(child);
                    } else {
                        const isTunnel = (uName.includes("TUNNEL") || uName.includes("TÜNEL") || uName === "TA" || uName === "TB" || uName.startsWith("TA_") || uName.startsWith("TB_"));
                        if (isTunnel) {
                            tunnelMeshes.push(child);
                        } else {
                            child.material = new THREE.MeshStandardMaterial({ color: 0x141E2D, roughness: 0.8 });
                        }
                    }
                }
            });

            const targetMeshes = [];
            rawSensors.forEach(child => {
                child.visible = false;
                const name = child.name; const uName = name.toUpperCase(); const sensorId = extractSensorId(name);
                let isCategory = false;
                if (payload.comp === "hoop" && uName.includes("-CS")) isCategory = true;
                else if (payload.comp === "axial") { if (uName.includes("-CS")) isCategory = false; else if (uName.includes("-S") || checkSensorData(sensorId, "axial").found) isCategory = true; }
                else if (payload.comp === "temp" && uName.includes("-TP")) isCategory = true;
                if (!isCategory) return;
                const dataInfo = checkSensorData(sensorId, payload.comp);
                const wPos = new THREE.Vector3(); child.getWorldPosition(wPos);
                targetMeshes.push({ mesh: child, pos: wPos, sensorName: dataInfo.key, hasData: dataInfo.found, val: dataInfo.val });
            });

            const finalSensors = [];
            targetMeshes.forEach(item => {
                let duplicate = null;
                for (let f of finalSensors) { if (f.pos.distanceTo(item.pos) < 0.12 && getCanonicalSensorId(f.sensorName) === getCanonicalSensorId(item.sensorName)) { duplicate = f; break; } }
                if (!duplicate) finalSensors.push(item);
                else if (!duplicate.hasData && item.hasData) { duplicate.hasData = true; duplicate.val = item.val; duplicate.sensorName = item.sensorName; duplicate.mesh = item.mesh; }
            });

            let alreadyHighlightedOne = false;
            finalSensors.forEach(item => {
                if (item.hasData || payload.showNoDataRed) {
                    const isCandidate = (payload.selectedSensor && payload.selectedSensor !== "Seçiniz..." && item.sensorName === payload.selectedSensor);
                    const isSelected = isCandidate && !alreadyHighlightedOne;
                    if (isSelected) alreadyHighlightedOne = true;

                    let sensorColor = 0xFFFFFF;
                    if (isSelected) sensorColor = 0xFFD700; else if (!item.hasData) sensorColor = 0xFF0033;

                    const sensorMat = new THREE.MeshBasicMaterial({ color: sensorColor, side: THREE.DoubleSide, transparent: false, opacity: 1.0, depthTest: true, depthWrite: true });
                    const wQuat = new THREE.Quaternion(); const wScale = new THREE.Vector3();
                    item.mesh.getWorldQuaternion(wQuat); item.mesh.getWorldScale(wScale);
                    const detachedMesh = new THREE.Mesh(item.mesh.geometry.clone(), sensorMat);
                    detachedMesh.position.copy(item.pos); detachedMesh.quaternion.copy(wQuat); detachedMesh.scale.copy(wScale);
                    detachedMesh.userData.sensorName = item.sensorName; detachedMesh.userData.val = item.hasData ? item.val : NaN; detachedMesh.userData.isUsable = item.hasData; detachedMesh.userData.isNoData = !item.hasData;
                    sensorScene.add(detachedMesh); interactiveSensors.push(detachedMesh);
                    if (isSelected) { selectedMeshRef = detachedMesh; updateHud(item.sensorName, item.val, item.hasData); }
                }
            });

            const interpolationSensors = [];
            interactiveSensors.forEach(sMesh => {
                if (sMesh.userData.isUsable && !sMesh.userData.isNoData) {
                    const uName = sMesh.userData.sensorName.toUpperCase();
                    const tun = uName.startsWith("TB") ? "TB" : (uName.startsWith("TA") ? "TA" : "ALL");
                    interpolationSensors.push({ pos: sMesh.position.clone(), val: sMesh.userData.val, tun: tun, name: sMesh.userData.sensorName });
                }
            });

            const R_SENSOR = 60.0; 
            tunnelMeshes.forEach(tMesh => {
                const geom = tMesh.geometry; if (!geom || !geom.attributes || !geom.attributes.position) return;
                const posAttr = geom.attributes.position; const colors = new Float32Array(posAttr.count * 3);
                const localV = new THREE.Vector3(); const worldV = new THREE.Vector3();
                const uName = tMesh.name.toUpperCase(); const isTB = uName.includes("TB"); const activeTun = isTB ? "TB" : "TA";
                let pool = interpolationSensors.filter(s => s.tun === activeTun || s.tun === "ALL");
                if (pool.length === 0) pool = interpolationSensors;

                tMesh.updateMatrixWorld(true);

                if (pool.length === 0) {
                    for (let i = 0; i < posAttr.count; i++) { const idx = i * 3; colors[idx] = 0.08; colors[idx + 1] = 0.11; colors[idx + 2] = 0.16; }
                } else {
                    for (let i = 0; i < posAttr.count; i++) {
                        localV.fromBufferAttribute(posAttr, i);
                        worldV.copy(localV).applyMatrix4(tMesh.matrixWorld);
                        let totalWeight = 0; let accumulatedVal = 0;
                        for (let j = 0; j < pool.length; j++) {
                            const s = pool[j]; const d = worldV.distanceTo(s.pos);
                            if (d < R_SENSOR) {
                                const normD = d / R_SENSOR;
                                const w = Math.pow(1.0 - normD, 1.3) / (Math.pow(d, 0.85) + 0.1);
                                accumulatedVal += s.val * w; totalWeight += w;
                            }
                        }
                        const idx = i * 3;
                        if (totalWeight > 0.00001) {
                            const interpolatedVal = accumulatedVal / totalWeight; const c = getColorForValue(interpolatedVal, payload.clim);
                            colors[idx] = c.r; colors[idx + 1] = c.g; colors[idx + 2] = c.b;
                        } else { colors[idx] = 0.08; colors[idx + 1] = 0.11; colors[idx + 2] = 0.16; }
                    }
                }
                geom.setAttribute('color', new THREE.BufferAttribute(colors, 3)); geom.attributes.color.needsUpdate = true;
                const isTransparent = payload.tunnelOpacity < 0.98;
                if (isTransparent) {
                    const depthMaskMat = new THREE.MeshBasicMaterial({ colorWrite: false, depthWrite: true, side: THREE.FrontSide });
                    const depthMaskMesh = new THREE.Mesh(geom, depthMaskMat); depthMaskMesh.renderOrder = 0; tMesh.add(depthMaskMesh);
                }
                tMesh.material = new THREE.MeshStandardMaterial({ color: 0xffffff, vertexColors: true, transparent: isTransparent, opacity: payload.tunnelOpacity, roughness: 0.20, metalness: 0.02, depthWrite: !isTransparent, side: THREE.FrontSide });
                tMesh.renderOrder = 1; tMesh.material.needsUpdate = true;
            });

            const boxTA = new THREE.Box3(); const boxTB = new THREE.Box3(); let hasTA = false, hasTB = false;
            tunnelMeshes.forEach(tm => {
                const u = tm.name.toUpperCase();
                if (u.includes("TB")) { boxTB.expandByObject(tm); hasTB = true; } else if (u.includes("TA")) { boxTA.expandByObject(tm); hasTA = true; }
            });

            const portalsGroup = new THREE.Group();
            if (hasTA) { const cA = boxTA.getCenter(new THREE.Vector3()); const sTA = createPortalMarker("TA"); sTA.position.set(cA.x, boxTA.max.y + 17.0, boxTA.min.z - 8.0); portalsGroup.add(sTA); }
            if (hasTB) { const cB = boxTB.getCenter(new THREE.Vector3()); const sTB = createPortalMarker("TB"); sTB.position.set(cB.x, boxTB.max.y + 17.0, boxTB.min.z - 8.0); portalsGroup.add(sTB); }
            scene.add(portalsGroup);

            // =========================================================
            // ЗЕРКАЛЬНЫЕ ЛИНЕЙКИ (МАСШТАБ 2X, 0 С КОНЧИКА)
            // =========================================================
            if (payload.showMeters) {
                const overallBox = new THREE.Box3(); 
                tunnelMeshes.forEach(tm => overallBox.expandByObject(tm));
                
                if (!overallBox.isEmpty()) {
                    const size = overallBox.getSize(new THREE.Vector3()); 
                    const rulerGroup = new THREE.Group();

                    const scale = 2.0; 

                    const isZAxis = size.z >= size.x; 
                    const length3D = isZAxis ? size.z : size.x; 
                    const startCoord = isZAxis ? overallBox.min.z : overallBox.min.x; 
                    const endCoord = isZAxis ? overallBox.max.z : overallBox.max.x;
                    
                    const stepReal = 10.0; 
                    const step3D = stepReal * scale; 
                    const stepsCount = Math.floor(length3D / step3D); 

                    const yRuler = overallBox.min.y - 0.2; 
                    
                    const lateralPos1 = isZAxis ? (overallBox.max.x + (3.5 * scale)) : (overallBox.max.z + (3.5 * scale));
                    const lateralPos2 = isZAxis ? (overallBox.min.x - (3.5 * scale)) : (overallBox.min.z - (3.5 * scale));

                    const linePoints1 = [];
                    const linePoints2 = [];
                    if (isZAxis) {
                        linePoints1.push(new THREE.Vector3(lateralPos1, yRuler, startCoord));
                        linePoints1.push(new THREE.Vector3(lateralPos1, yRuler, endCoord));
                        linePoints2.push(new THREE.Vector3(lateralPos2, yRuler, startCoord));
                        linePoints2.push(new THREE.Vector3(lateralPos2, yRuler, endCoord));
                    } else {
                        linePoints1.push(new THREE.Vector3(startCoord, yRuler, lateralPos1));
                        linePoints1.push(new THREE.Vector3(endCoord, yRuler, lateralPos1));
                        linePoints2.push(new THREE.Vector3(startCoord, yRuler, lateralPos2));
                        linePoints2.push(new THREE.Vector3(endCoord, yRuler, lateralPos2));
                    }

                    const axisMat = new THREE.LineBasicMaterial({ color: 0x00E5FF, linewidth: 3 });
                    rulerGroup.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(linePoints1), axisMat));
                    rulerGroup.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(linePoints2), axisMat));

                    const tickSize = 0.8 * scale;

                    for (let i = 0; i <= stepsCount; i++) {
                        const currentPos3D = endCoord - (i * step3D); 
                        const distanceText = (i * stepReal).toFixed(0) + " m"; 

                        const tickPoints1 = [];
                        if (isZAxis) {
                            tickPoints1.push(new THREE.Vector3(lateralPos1 - tickSize, yRuler, currentPos3D));
                            tickPoints1.push(new THREE.Vector3(lateralPos1 + tickSize, yRuler, currentPos3D));
                        } else {
                            tickPoints1.push(new THREE.Vector3(currentPos3D, yRuler, lateralPos1 - tickSize));
                            tickPoints1.push(new THREE.Vector3(currentPos3D, yRuler, lateralPos1 + tickSize));
                        }
                        rulerGroup.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(tickPoints1), axisMat));
                        
                        const label1 = createRulerLabel(distanceText);
                        label1.scale.set(2.4 * scale, 1.2 * scale, 1);
                        if (isZAxis) label1.position.set(lateralPos1 + (2.4 * scale), yRuler + 0.4, currentPos3D); 
                        else label1.position.set(currentPos3D, yRuler + 0.4, lateralPos1 + (2.4 * scale));
                        rulerGroup.add(label1);

                        const tickPoints2 = [];
                        if (isZAxis) {
                            tickPoints2.push(new THREE.Vector3(lateralPos2 - tickSize, yRuler, currentPos3D));
                            tickPoints2.push(new THREE.Vector3(lateralPos2 + tickSize, yRuler, currentPos3D));
                        } else {
                            tickPoints2.push(new THREE.Vector3(currentPos3D, yRuler, lateralPos2 - tickSize));
                            tickPoints2.push(new THREE.Vector3(currentPos3D, yRuler, lateralPos2 + tickSize));
                        }
                        rulerGroup.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(tickPoints2), axisMat));
                        
                        const label2 = createRulerLabel(distanceText);
                        label2.scale.set(2.4 * scale, 1.2 * scale, 1);
                        if (isZAxis) label2.position.set(lateralPos2 - (2.4 * scale), yRuler + 0.4, currentPos3D); 
                        else label2.position.set(currentPos3D, yRuler + 0.4, lateralPos2 - (2.4 * scale));
                        rulerGroup.add(label2);
                    }
                    scene.add(rulerGroup);
                }
            }

            // ====================================================================
            // ЛОГИКА КАМЕРЫ
            // ====================================================================
            const lastSelected = (function(){ try{ return window.sessionStorage.getItem('loggis_sensor_v7'); }catch(e){return null;} })();
            const isNewSensorSelected = (payload.selectedSensor && payload.selectedSensor !== "Seçiniz..." && payload.selectedSensor !== lastSelected);

            if (selectedMeshRef && isNewSensorSelected) {
                try{ window.sessionStorage.setItem('loggis_sensor_v7', payload.selectedSensor); }catch(e){}
                
                isModelLoaded = true;
                flyCameraTo(selectedMeshRef, true);
            } else {
                if (!isNewSensorSelected && payload.selectedSensor === "Seçiniz...") {
                    try{ window.sessionStorage.removeItem('loggis_sensor_v7'); }catch(e){}
                }

                let cameraRestored = false;
                try {
                    const savedStr = window.sessionStorage.getItem('loggis_cam_v7');
                    if (savedStr) {
                        const st = JSON.parse(savedStr);
                        if (st && st.pos && st.tgt && !isNaN(st.pos[0]) && !isNaN(st.tgt[0])) {
                            camera.position.fromArray(st.pos);
                            controls.target.fromArray(st.tgt);
                            controls.update();
                            cameraRestored = true;
                        }
                    }
                } catch(e) {}
                
                if (!cameraRestored) {
                    const tunnelBox = new THREE.Box3(); 
                    if (tunnelMeshes.length > 0) {
                        tunnelMeshes.forEach(tm => {
                            if(tm.geometry) tm.geometry.computeBoundingBox();
                            tunnelBox.expandByObject(tm);
                        });
                    } else { 
                        model.traverse(c => { if(c.isMesh && c.geometry) c.geometry.computeBoundingBox(); });
                        tunnelBox.setFromObject(model); 
                    }
                    
                    if (!tunnelBox.isEmpty()) {
                        const center = tunnelBox.getCenter(new THREE.Vector3()); 
                        const size = tunnelBox.getSize(new THREE.Vector3()); 
                        const maxDim = Math.max(size.x, size.y, size.z, 20.0);
                        controls.target.copy(center); 
                        
                        const fov = camera.fov * (Math.PI / 180);
                        let cameraZ = Math.abs(maxDim / Math.sin(fov / 2)) * 0.25;
                        
                        camera.position.set(center.x - maxDim * 0.1, center.y + maxDim * 0.1, center.z + cameraZ); 
                        controls.update();
                    }
                }
                
                isModelLoaded = true;
                saveCamState();
            }

        }, undefined, function(err) { loaderText.innerHTML = "Model yüklenirken hata oluştu!"; console.error(err); });

        function updateHud(name, val, isUsable) {
            selectedHud.style.display = 'block'; hudName.innerText = name;
            if (isUsable && val !== undefined && !isNaN(val)) { const valTxt = (val > 0 ? "+" + val.toFixed(2) : val.toFixed(2)) + " " + payload.unit; hudVal.innerText = valTxt; hudVal.style.color = "#00E5FF"; }
            else { hudVal.innerText = "-"; hudVal.style.color = "#FF0033"; }
        }

        function flyCameraTo(targetMesh, animate = true) {
            const targetPos = targetMesh.position.clone();
            const offsetDir = new THREE.Vector3(targetPos.x, 0, targetPos.z).normalize();
            if (offsetDir.length() === 0) offsetDir.set(1, 0, 0);
            const endCamPos = targetPos.clone().add(offsetDir.multiplyScalar(4.0)).add(new THREE.Vector3(0, 1.8, 0));
            if (!animate) { 
                camera.position.copy(endCamPos); controls.target.copy(targetPos); controls.update(); 
                saveCamState();
                return; 
            }
            new TWEEN.Tween(controls.target).to(targetPos, 1400).easing(TWEEN.Easing.Cubic.InOut).start();
            new TWEEN.Tween(camera.position).to(endCamPos, 1400).easing(TWEEN.Easing.Cubic.InOut).onUpdate(() => controls.update())
            .onComplete(saveCamState).start();
        }

        function getIntersectedSensor(e) {
            const rect = renderer.domElement.getBoundingClientRect();
            const clientX = e.clientX !== undefined ? e.clientX : (e.touches && e.touches[0] ? e.touches[0].clientX : (e.changedTouches ? e.changedTouches[0].clientX : 0));
            const clientY = e.clientY !== undefined ? e.clientY : (e.touches && e.touches[0] ? e.touches[0].clientY : (e.changedTouches ? e.changedTouches[0].clientY : 0));
            mouse.x = ((clientX - rect.left) / rect.width) * 2 - 1; mouse.y = -((clientY - rect.top) / rect.height) * 2 + 1;
            raycaster.setFromCamera(mouse, camera); const intersects = raycaster.intersectObjects(interactiveSensors, true);
            if (intersects.length > 0) { let obj = intersects[0].object; while (obj && !obj.userData.sensorName && obj.parent) { obj = obj.parent; } return (obj && (obj.userData.isUsable || obj.userData.isNoData)) ? obj : null; }
            return null;
        }

        function handleSensorSelection(sensorMesh) {
            if (!sensorMesh) return;
            const sensorName = sensorMesh.userData.sensorName; const sensorVal = sensorMesh.userData.val; const isUsable = sensorMesh.userData.isUsable;
            interactiveSensors.forEach(m => { if (m === sensorMesh) m.material.color.setHex(0xFFD700); else if (m.userData.isUsable) m.material.color.setHex(0xFFFFFF); else m.material.color.setHex(0xFF0033); });
            flyCameraTo(sensorMesh, true); updateHud(sensorName, sensorVal, isUsable);
        }

        window.addEventListener('click', function(e) { const sensorMesh = getIntersectedSensor(e); if (sensorMesh) handleSensorSelection(sensorMesh); });
        let touchStartTime = 0; window.addEventListener('touchstart', function() { touchStartTime = Date.now(); }, { passive: true });
        window.addEventListener('touchend', function(e) { if (Date.now() - touchStartTime < 250) { const sensorMesh = getIntersectedSensor(e); if (sensorMesh) handleSensorSelection(sensorMesh); } });
        window.addEventListener('mousemove', function(e) {
            const sensorMesh = getIntersectedSensor(e);
            if (sensorMesh) {
                const name = sensorMesh.userData.sensorName; const val = sensorMesh.userData.val; const isUsable = sensorMesh.userData.isUsable; const isNoData = sensorMesh.userData.isNoData;
                tooltip.style.display = 'block'; tooltip.style.left = (e.clientX + 14) + 'px'; tooltip.style.top = (e.clientY + 14) + 'px';
                if (isUsable) {
                    const valTxt = (val > 0 ? "+" + val : val) + " " + payload.unit;
                    tooltip.innerHTML = '<b>' + name + '</b><br><span style="color:#00E5FF;">' + labelPrefix + valTxt + '</span><br><span style="color:#8397AD; font-size:11px;">(Odaklanmak için tıkla)</span>';
                    renderer.domElement.style.cursor = 'pointer';
                } else if (isNoData) {
                    tooltip.innerHTML = '<b>' + name + '</b><br><span style="color:#FF0033; font-weight:700;">Durum: -</span><br><span style="color:#8397AD; font-size:11px;">(Odaklanmak için tıkla)</span>';
                    renderer.domElement.style.cursor = 'pointer';
                }
            } else {
                tooltip.style.display = 'none';
                renderer.domElement.style.cursor = 'default';
            }
        });
        window.addEventListener('resize', function() { camera.aspect = container.clientWidth / container.clientHeight; camera.updateProjectionMatrix(); renderer.setSize(container.clientWidth, container.clientHeight); });
        (function animate(time) { requestAnimationFrame(animate); TWEEN.update(time); controls.update(); renderer.clear(); renderer.render(scene, camera); renderer.clearDepth(); renderer.render(sensorScene, camera); })();
    </script>
</body>
</html>"""

        final_html = raw_template.replace("__INJECT_PAYLOAD__", json_payload).replace("__INJECT_MODEL__", model_b64)
        st.components.v1.html(final_html, height=600, scrolling=False)

# ---------------------------------------------------------
# АНАЛИТИЧЕСКАЯ ТАБЛИЦА (FARK RAPORU)
# ---------------------------------------------------------
if compare_mode and table_data:
    st.markdown("---")
    st.markdown(f"### Fark Raporu ({target_timestamp} ➔ {latest_timestamp})")
    
    df = pd.DataFrame(table_data)
    df = df.sort_values(by="Sensör No").reset_index(drop=True)
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=400,
        column_config={
            "Sensör No": st.column_config.TextColumn("Sensör No", width="medium"),
            "Arşiv Değeri": st.column_config.TextColumn(f"Geçmiş ({target_timestamp})", width="small"),
            "Güncel Değer": st.column_config.TextColumn(f"Şimdi ({latest_timestamp})", width="small"),
            "Fark (Δ)": st.column_config.TextColumn("Fark (Δ)", width="small"),
        }
    )
