#!/usr/bin/env python3
"""
Generate terminal screenshot of budget demo
"""

import subprocess
import os

os.chdir('/home/openclaw/azure-ai-infra-platform')
env = os.environ.copy()
env['PYTHONPATH'] = '/home/openclaw/azure-ai-infra-platform'

# Run demo and capture screenshot
result = subprocess.run(
    ['script', '-c', 'python3 docs/budget_enforcement_demo.py', '/tmp/budget_demo_terminal.txt'],
    capture_output=True,
    text=True,
    env=env
)

print(f"✓ Terminal output captured to /tmp/budget_demo_terminal.txt")

# Now take a screenshot
screenshot_path = '/tmp/budget_demo_screenshot.png'

# Try with scrot
subprocess.run(['scrot', screenshot_path], capture_output=True)

if os.path.exists(screenshot_path):
    print(f"✓ Screenshot saved to {screenshot_path}")
    print(f"File size: {os.path.getsize(screenshot_path)} bytes")
else:
    print(f"✗ Screenshot not created. Trying alternative method...")
    # Alternative: use xwd and convert
    subprocess.run(['xwd', '-root', '-out', '/tmp/xdm.xwd'], capture_output=True)
    subprocess.run(['convert', '/tmp/xdm.xwd', screenshot_path], capture_output=True)
    if os.path.exists(screenshot_path):
        print(f"✓ Screenshot saved via convert: {screenshot_path}")