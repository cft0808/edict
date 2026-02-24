#!/usr/bin/env python3
"""Record a demo video of the dashboard and convert to GIF."""
from playwright.sync_api import sync_playwright
import subprocess, os, time

ROOT = os.path.join(os.path.dirname(__file__), '..')
VIDEO_DIR = os.path.join(ROOT, 'docs', '_video_tmp')
OUTPUT_GIF = os.path.join(ROOT, 'docs', 'demo.gif')
URL = 'http://localhost:7891'

def main():
    os.makedirs(VIDEO_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={'width': 1280, 'height': 720},
            device_scale_factor=2,
            color_scheme='dark',
            record_video_dir=VIDEO_DIR,
            record_video_size={'width': 1280, 'height': 720},
        )
        page = ctx.new_page()

        # === Scene 1: Ceremony (3s) ===
        print('🎬 Scene 1: Ceremony...')
        page.goto(URL)
        page.wait_for_timeout(500)
        page.evaluate("localStorage.removeItem('openclaw_court_date')")
        page.reload()
        page.wait_for_timeout(3500)

        # === Scene 2: Kanban overview (3s) ===
        print('📋 Scene 2: Kanban...')
        # Ceremony should have auto-dismissed by now, or skip it
        page.evaluate("localStorage.setItem('openclaw_court_date', new Date().toISOString().substring(0,10))")
        page.reload()
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(2000)
        # Slow scroll down to show tasks
        page.mouse.wheel(0, 300)
        page.wait_for_timeout(1500)
        page.mouse.wheel(0, -300)
        page.wait_for_timeout(500)

        # === Scene 3: Click a task (3s) ===
        print('📜 Scene 3: Task detail...')
        cards = page.locator('.edict-card')
        if cards.count() > 0:
            cards.first.click()
            page.wait_for_timeout(2500)
            page.keyboard.press('Escape')
            page.wait_for_timeout(500)

        # === Scene 4: Monitor (2s) ===
        print('🔭 Scene 4: Monitor...')
        page.click('[data-tab="monitor"]')
        page.wait_for_timeout(2000)

        # === Scene 5: Memorials (2s) ===
        print('📜 Scene 5: Memorials...')
        page.click('[data-tab="memorials"]')
        page.wait_for_timeout(2000)

        # === Scene 6: Templates (2s) ===
        print('📜 Scene 6: Templates...')
        page.click('[data-tab="templates"]')
        page.wait_for_timeout(2000)

        # === Scene 7: Officials (2s) ===
        print('👥 Scene 7: Officials...')
        page.click('[data-tab="officials"]')
        page.wait_for_timeout(2000)

        # === Scene 8: Models (1.5s) ===
        print('⚙️ Scene 8: Models...')
        page.click('[data-tab="models"]')
        page.wait_for_timeout(1500)

        # === Scene 9: Back to Kanban (1s) ===
        print('📋 Scene 9: Back to kanban...')
        page.click('[data-tab="edicts"]')
        page.wait_for_timeout(1500)

        # Close context to finalize video
        page.close()
        ctx.close()
        browser.close()

    # Find the recorded video
    videos = [f for f in os.listdir(VIDEO_DIR) if f.endswith('.webm')]
    if not videos:
        print('❌ No video recorded!')
        return

    video_path = os.path.join(VIDEO_DIR, videos[0])
    print(f'🎥 Video: {video_path} ({os.path.getsize(video_path) / 1024 / 1024:.1f} MB)')

    # Convert to GIF using ffmpeg
    # Two-pass: generate palette first for quality, then apply
    palette_path = os.path.join(VIDEO_DIR, 'palette.png')

    print('🎨 Generating palette...')
    subprocess.run([
        'ffmpeg', '-y', '-i', video_path,
        '-vf', 'fps=12,scale=800:-1:flags=lanczos,palettegen=max_colors=128',
        palette_path
    ], capture_output=True)

    print('🖼️ Converting to GIF...')
    subprocess.run([
        'ffmpeg', '-y', '-i', video_path, '-i', palette_path,
        '-lavfi', 'fps=12,scale=800:-1:flags=lanczos [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=3',
        OUTPUT_GIF
    ], capture_output=True)

    size_mb = os.path.getsize(OUTPUT_GIF) / 1024 / 1024
    print(f'✅ GIF saved: {OUTPUT_GIF} ({size_mb:.1f} MB)')

    if size_mb > 5:
        print('⚠️ GIF is over 5MB, re-encoding with lower quality...')
        subprocess.run([
            'ffmpeg', '-y', '-i', video_path,
            '-vf', 'fps=10,scale=640:-1:flags=lanczos,palettegen=max_colors=64',
            palette_path
        ], capture_output=True)
        subprocess.run([
            'ffmpeg', '-y', '-i', video_path, '-i', palette_path,
            '-lavfi', 'fps=10,scale=640:-1:flags=lanczos [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=5',
            OUTPUT_GIF
        ], capture_output=True)
        size_mb = os.path.getsize(OUTPUT_GIF) / 1024 / 1024
        print(f'✅ Re-encoded GIF: {size_mb:.1f} MB')

    # Cleanup
    import shutil
    shutil.rmtree(VIDEO_DIR, ignore_errors=True)
    print('🧹 Cleaned up temp files')

if __name__ == '__main__':
    main()
