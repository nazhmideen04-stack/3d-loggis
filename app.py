import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://loggis2.com/?company-id=20ce6d9f-398b-43b3-a452-3580dae39122&project-id=2d381d12-d966-4c90-a7c8-c90d6f758ae0&token-id=6e73d15f-0b2f-4d93-a152-3464f7450e50")
    page.get_by_text("Types").click()
    page.get_by_role("combobox").nth(1).select_option("TABLE_ROW_DATE")
    page.get_by_role("combobox").first.select_option("ALL")
    page.get_by_role("listbox").select_option("Longitudinal Strains")

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
