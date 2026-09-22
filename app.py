@st.cache_data(ttl=600)
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

            # 1. Открываем меню Types
            types_btn = page.locator("text=Types").first
            types_btn.wait_for(state="visible", timeout=45000)
            types_btn.click(force=True)
            page.wait_for_timeout(1000)

            # 2. Кликаем по названию категории в кастомном выпадающем списке
            opt = page.locator(f"text={cat['name']}").last
            opt.wait_for(state="visible", timeout=20000)
            opt.click(force=True)
            page.wait_for_timeout(1000)

            # Закрываем выпадающий список кликом вне его
            try:
                page.keyboard.press("Escape")
            except Exception:
                pass
            page.wait_for_timeout(500)

            # 3. Фильтры: Duration=ALL, Display=TABLE_MOST_RECENT, Processor=NONE
            combos = page.get_by_role("combobox")
            combos.first.wait_for(state="visible", timeout=20000)
            combos.first.select_option("ALL")
            page.wait_for_timeout(1000)

            combos.nth(1).select_option("TABLE_MOST_RECENT")
            page.wait_for_timeout(1500)

            if combos.count() >= 3:
                try:
                    combos.nth(2).select_option("NONE")
                except Exception:
                    pass
                page.wait_for_timeout(800)

            # 4. Ожидание таблицы и фильтрация строк
            table_loc = page.locator("table, [role='grid'], .table").first
            table_loc.wait_for(state="visible", timeout=45000)

            for _ in range(20):
                txt = page.locator("table tbody, [role='rowgroup']").inner_text()
                if cat["tag"] in txt:
                    break
                page.wait_for_timeout(1000)

            val_map = {}
            date_str = ""
            rows = page.locator("table tbody tr, [role='row']").all()

            for r in rows:
                cols = [td.inner_text().strip() for td in r.locator("td, [role='gridcell']").all()]
                if len(cols) >= 3 and cat["tag"] in cols[1]:
                    date_str = cols[0]
                    v = clean_num(cols[2])
                    if not np.isnan(v):
                        val_map[cols[1]] = v

            page.close()
            results[cat["key"]] = {"values": val_map, "date": date_str}

        context.close()
        browser.close()

    return results
