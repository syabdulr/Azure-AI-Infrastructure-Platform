#!/usr/bin/env python3
"""
Share flowchart info to Telegram
"""

import json
import requests

# Load Telegram bot credentials
with open('/home/openclaw/telegram_bot_credentials.json', 'r') as f:
    creds = json.load(f)

bot_token = creds['bot_token']
chat_id = creds['chat_id']

# Message to share
message = """🎨 Visual Element Ready!

Budget Enforcement Flowchart HTML

Created an interactive Mermaid.js flowchart showing:

📊 Flow Steps:
1. API Request → Budget Check
2. Cost Accumulation → Threshold Detection
3. 80% Warning (Yellow)
4. 90% Critical (Orange)
5. 100% Exceeded (Red)
6. Automatic Provider Pause
7. Report Generation

File Location: docs/budget_enforcement_flowchart.html

Rendering:
- Browser-based Mermaid.js diagram
- Color-coded alerts (yellow → orange → red)
- Decision points clearly marked
- Professional dark theme

For LinkedIn Post:
- Take screenshot of HTML in browser
- Combine with demo terminal output
- Shows system architecture + working demo

Perfect visual complement to the LinkedIn post! 🚀"""

url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
response = requests.post(url, data={
    'chat_id': chat_id,
    'text': message,
    'parse_mode': 'Markdown'
})

if response.status_code == 200:
    print("✓ Message shared to Telegram")
else:
    print(f"✗ Failed to send: {response.text}")