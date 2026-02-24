#!/usr/bin/env python3
"""Take all dashboard screenshots for the README using Playwright."""
from playwright.sync_api import sync_playwright
import time, os

SHOTS = os.path.join(os.path.dirname(__file__), '..', 'docs', 'screenshots')
URL = 'http://localhost:7891'

def main():
    os.makedirs(SHOTS, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            device_scale_factor=2,
            color_scheme='dark',
        )
        page = ctx.new_page()

        # ── Clear ceremony localStorage so it doesn't show on every load
        page.goto(URL)
        page.evaluate("localStorage.setItem('openclaw_court_date', new Date().toISOString().substring(0,10))")
        page.reload()
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(2000)

        # 1. Kanban main (default tab = edicts)
        print('📋 01 kanban...')
        page.screenshot(path=os.path.join(SHOTS, '01-kanban-main.png'), full_page=False)

        # 2. Monitor (省部调度)
        print('🔭 02 monitor...')
        page.click('[data-tab="monitor"]')
        page.wait_for_timeout(800)
        page.screenshot(path=os.path.join(SHOTS, '02-monitor.png'), full_page=False)

        # 3. Task detail - click first task card
        print('📜 03 task detail...')
        page.click('[data-tab="edicts"]')
        page.wait_for_timeout(500)
        cards = page.locator('.edict-card')
        if cards.count() > 0:
            cards.first.click()
            page.wait_for_timeout(800)
            page.screenshot(path=os.path.join(SHOTS, '03-task-detail.png'), full_page=False)
            # Close modal
            page.keyboard.press('Escape')
            page.wait_for_timeout(300)

        # 4. Model config
        print('⚙️ 04 models...')
        page.click('[data-tab="models"]')
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(SHOTS, '04-model-config.png'), full_page=False)

        # 5. Skills config
        print('🛠️ 05 skills...')
        page.click('[data-tab="skills"]')
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(SHOTS, '05-skills-config.png'), full_page=False)

        # 6. Officials overview
        print('👥 06 officials...')
        page.click('[data-tab="officials"]')
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(SHOTS, '06-official-overview.png'), full_page=False)

        # 7. Sessions
        print('💬 07 sessions...')
        page.click('[data-tab="sessions"]')
        page.wait_for_timeout(800)
        page.screenshot(path=os.path.join(SHOTS, '07-sessions.png'), full_page=False)

        # 8. Memorials
        print('📜 08 memorials...')
        page.click('[data-tab="memorials"]')
        page.wait_for_timeout(800)
        page.screenshot(path=os.path.join(SHOTS, '08-memorials.png'), full_page=False)

        # 9. Templates
        print('📜 09 templates...')
        page.click('[data-tab="templates"]')
        page.wait_for_timeout(800)
        page.screenshot(path=os.path.join(SHOTS, '09-templates.png'), full_page=False)

        # 10. Morning briefing
        print('📰 10 morning...')
        page.click('[data-tab="morning"]')
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(SHOTS, '10-morning-briefing.png'), full_page=False)

        # 11. Ceremony - clear date then reload
        print('🎬 11 ceremony...')
        page.evaluate("localStorage.removeItem('openclaw_court_date')")
        page.reload()
        page.wait_for_timeout(2500)
        page.screenshot(path=os.path.join(SHOTS, '11-ceremony.png'), full_page=False)

        browser.close()
    print('✅ All screenshots saved to', SHOTS)

if __name__ == '__main__':
    main()
