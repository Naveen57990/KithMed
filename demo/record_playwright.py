#!/usr/bin/env python3
"""
Record 1080p high-fidelity demo video using Playwright with in-DOM live subtitle HUD.
"""

import os
import json
import asyncio
from playwright.async_api import async_playwright

DEMO_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.abspath(os.path.join(DEMO_DIR, "..", "web"))
HTML_URL = f"file://{os.path.join(WEB_DIR, 'index.html')}"

async def record_demo():
    timeline_path = os.path.join(DEMO_DIR, "timeline.json")
    with open(timeline_path, "r") as f:
        timeline = json.load(f)

    total_duration = timeline["total_duration"]
    scenes = timeline["scenes"]
    print(f"Recording video for duration: {total_duration}s across {len(scenes)} scenes...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--hide-scrollbars",
                "--window-size=1920,1080"
            ]
        )
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
            record_video_dir=DEMO_DIR,
            record_video_size={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        await page.goto(HTML_URL)
        await page.wait_for_load_state("networkidle")

        # Inject in-DOM Subtitle HUD
        await page.evaluate("""
            const hud = document.createElement('div');
            hud.id = 'demo-subtitle-hud';
            hud.style.position = 'fixed';
            hud.style.bottom = '30px';
            hud.style.left = '50%';
            hud.style.transform = 'translateX(-50%)';
            hud.style.width = '75%';
            hud.style.maxWidth = '1100px';
            hud.style.padding = '14px 26px';
            hud.style.backgroundColor = 'rgba(15, 23, 42, 0.92)';
            hud.style.border = '2px solid #2563eb';
            hud.style.borderRadius = '12px';
            hud.style.boxShadow = '0 10px 30px rgba(0, 0, 0, 0.5), 0 0 20px rgba(37, 99, 235, 0.4)';
            hud.style.color = '#ffffff';
            hud.style.fontFamily = "'Plus Jakarta Sans', sans-serif";
            hud.style.fontSize = '18px';
            hud.style.fontWeight = '600';
            hud.style.lineHeight = '1.4';
            hud.style.textAlign = 'center';
            hud.style.zIndex = '99999';
            hud.style.backdropFilter = 'blur(8px)';
            hud.style.transition = 'opacity 0.3s ease';
            hud.innerHTML = '<span style="color: #60a5fa; font-family: monospace; font-weight: 800; margin-right: 8px;">[KITHMED ENGINE]</span> Initializing...';
            document.body.appendChild(hud);

            window.setDemoSubtitle = function(text) {
                const el = document.getElementById('demo-subtitle-hud');
                if (el) {
                    el.innerHTML = '<span style="color: #60a5fa; font-family: monospace; font-weight: 800; margin-right: 8px;">[KITHMED ENGINE]</span> ' + text;
                }
            };
        """)

        # Scene 1: Intro
        s1 = scenes[0]
        await page.evaluate(f"window.setDemoSubtitle({json.dumps(s1['text'])});")
        await asyncio.sleep(2.0)
        # Toggle theme back and forth to show responsiveness
        await page.click("#themeToggle")
        await asyncio.sleep(2.0)
        await page.click("#themeToggle")
        await asyncio.sleep(max(1.0, s1["duration"] - 4.5))

        # Scene 2: Sepsis
        s2 = scenes[1]
        await page.evaluate(f"window.setDemoSubtitle({json.dumps(s2['text'])});")
        await page.select_option("#casePreset", "sepsis")
        await asyncio.sleep(2.0)
        # Nudge HR and temp
        await page.fill("#input_hr", "130")
        await page.dispatch_event("#input_hr", "input")
        await asyncio.sleep(1.5)
        await page.fill("#input_temp", "39.8")
        await page.dispatch_event("#input_temp", "input")
        await asyncio.sleep(max(1.0, s2["duration"] - 3.8))

        # Scene 3: Trauma
        s3 = scenes[2]
        await page.evaluate(f"window.setDemoSubtitle({json.dumps(s3['text'])});")
        await page.select_option("#casePreset", "trauma")
        await asyncio.sleep(2.0)
        # Adjust SBP downwards to demonstrate shock index escalation
        await page.fill("#input_sbp", "78")
        await page.dispatch_event("#input_sbp", "input")
        await asyncio.sleep(max(1.0, s3["duration"] - 2.5))

        # Scene 4: Conformal Uncertainty
        s4 = scenes[3]
        await page.evaluate(f"window.setDemoSubtitle({json.dumps(s4['text'])});")
        await page.select_option("#casePreset", "boundary")
        await asyncio.sleep(2.0)
        # Adjust SpO2 slightly
        await page.fill("#input_spo2", "93")
        await page.dispatch_event("#input_spo2", "input")
        await asyncio.sleep(max(1.0, s4["duration"] - 2.5))

        # Scene 5: Offline Pass & Closing
        s5 = scenes[4]
        await page.evaluate(f"window.setDemoSubtitle({json.dumps(s5['text'])});")
        await page.click("#exportPassBtn")
        await asyncio.sleep(3.0)
        await page.click("#closeModalBtn")
        await asyncio.sleep(1.5)
        await page.click("#copyJsonBtn")
        await asyncio.sleep(max(1.0, s5["duration"] - 5.0))

        # Close page to flush video
        video_path = await page.video.path()
        await page.close()
        await context.close()
        await browser.close()

        print(f"Raw video recorded at: {video_path}")
        # Rename raw video
        target_raw = os.path.join(DEMO_DIR, "raw_recording.webm")
        if os.path.exists(target_raw):
            os.remove(target_raw)
        os.rename(video_path, target_raw)
        print(f"Moved raw video to: {target_raw}")

if __name__ == "__main__":
    asyncio.run(record_demo())
