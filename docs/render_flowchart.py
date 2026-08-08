"""Render flowchart to PNG."""

import asyncio
from playwright.async_api import async_playwright
import os

async def render_flowchart():
    """Render HTML flowchart to PNG."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Get absolute path
        html_path = os.path.abspath("/home/openclaw/azure-ai-infra-platform/docs/flowchart.html")
        png_path = os.path.abspath("/home/openclaw/azure-ai-infra-platform/docs/flowchart.png")

        # Load HTML
        await page.goto(f"file://{html_path}")
        await page.wait_for_load_state("networkidle")

        # Take screenshot
        await page.screenshot(path=png_path, type="png", full_page=False)

        await browser.close()
        return png_path

# Run
png_path = asyncio.run(render_flowchart())
print(f"✅ Flowchart rendered to: {png_path}")