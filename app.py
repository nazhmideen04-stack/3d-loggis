import os
import re
from playwright.sync_api import sync_playwright

URL = "https://loggis2.com/?company-id=20ce6d9f-398b-43b3-a452-3580dae39122&project-id=2d381d12-d966-4c90-a7c8-c90d6f758ae0&token-id=6e73d15f-0b2f-4d93-a152-3464f7450e50"

def download_all_csvs():
    os.makedirs("downloaded_csvs", exist_ok=True)
    
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        
        print("🌐 Сайт открывается...")
        page.goto(URL)
        page.wait_for_timeout(3000)
        
        print("⚙️ Установка режима ALL...")
        page.get_by_role("combobox").first.select_option("ALL")
        page.wait_for_timeout(1500)
        
        print("📂 Открытие вкладки Types...")
        page.get_by_text("Types").click()
        page.wait_for_timeout(1000)
        
        categories = ["Longitudinal Strains", "Othoradial Strains", "Temperature"]
        
        for cat in categories:
            print(f"📥 Скачивание категории: {cat}...")
            try:
                page.get_by_role("listbox").select_option(cat)
                page.wait_for_timeout(2000)
                
                with page.expect_download() as download_info:
                    try:
                        with page.expect_popup() as page1_info:
                            page.get_by_text("🠋CSV").click()
                        page1 = page1_info.value
                        page1.close()
                    except:
                        page.get_by_text("🠋CSV").click()
                
                download = download_info.value
                file_name = f"{cat.replace(' ', '_').lower()}.csv"
                save_path = os.path.join("downloaded_csvs", file_name)
                download.save_as(save_path)
                print(f"✅ Успешно сохранено: {save_path}")
            except Exception as e:
                print(f"❌ Ошибка при скачивании {cat}: {e}")
                
        context.close()
        browser.close()
        print("🏁 Все файлы успешно загружены!")

if __name__ == "__main__":
    download_all_csvs()
