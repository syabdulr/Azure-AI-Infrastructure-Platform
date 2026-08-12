#!/usr/bin/env python3
"""
Send LinkedIn message to LinkedInProfMediaAgent bot with budget demo output
"""

import json
import subprocess
import os
import requests

# Set up environment
os.chdir('/home/openclaw/azure-ai-infra-platform')
env = os.environ.copy()
env['PYTHONPATH'] = '/home/openclaw/azure-ai-infra-platform'

# Load and run the demo
demo_output = subprocess.run(
    ['python3', 'docs/budget_enforcement_demo.py'],
    capture_output=True,
    text=True,
    env=env
).stdout

# Load Telegram bot credentials
with open('/home/openclaw/telegram_bot_credentials.json', 'r') as f:
    creds = json.load(f)

bot_token = creds['bot_token']
chat_id = creds['chat_id']

# Send to Telegram bot
message = f"""🚀 Budget Enforcement Demo Output

```bash
{demo_output}
```

This demo shows:
✅ 80% alert threshold
✅ 90% critical warning
✅ 100% budget exceeded
✅ Automatic request blocking
✅ Comprehensive usage reports
✅ Budget reset & recovery

Ready for LinkedIn post!"""

url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
response = requests.post(url, data={
    'chat_id': chat_id,
    'text': message,
    'parse_mode': 'Markdown'
})

if response.status_code == 200:
    print("✓ Demo sent to LinkedInProfMediaAgent bot")
else:
    print(f"✗ Failed to send: {response.text}")