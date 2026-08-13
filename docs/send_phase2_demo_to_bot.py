#!/usr/bin/env python3
"""
Send Phase 2 visual + draft post to LinkedInProfMediaAgent bot.
Photo with short caption, then full draft post as separate message.
"""

import json
import requests

with open('/home/openclaw/telegram_bot_credentials.json', 'r') as f:
    creds = json.load(f)

bot_token = creds['bot_token']
chat_id = creds['chat_id']
BASE = f"https://api.telegram.org/bot{bot_token}"

# 1. Send photo with short caption
print("Sending visual...")
with open('/tmp/phase2_demo_visual.png', 'rb') as photo:
    photo_resp = requests.post(
        f"{BASE}/sendPhoto",
        data={
            "chat_id": chat_id,
            "caption": "📊 LIVE DEMO: Gateway routing requests, cache hits, budget alerts firing, A/B test results, and Prometheus export — all real code paths, no mocks."
        },
        files={"photo": photo}
    )
print(f"Photo: {photo_resp.status_code}")

# 2. Send draft post as separate message
draft_post = """📋 DRAFT LINKEDIN POST — Phase 2 Complete

Just shipped all 6 features of Phase 2 for my Multi-Provider AI Gateway! 🎉

🎯 The Problem
Teams using multiple AI providers (Azure OpenAI, OpenAI) face:
• Inconsistent response formats
• Uncontrolled costs
• No data-driven routing decisions
• No visibility into performance

💡 The Solution — 6 Production-Ready Features

✅ Response Normalization
Unified output format across providers with adapters

✅ Multi-Provider Caching (30-40% cost reduction)
SQLite-backed cache with TTL management and hit/miss metrics

✅ Budget Enforcement (100% cost control)
Per-provider daily/monthly limits with 80/90/100% alerting and auto-throttling

✅ Custom Routing Rules
9 operators, 4 priority levels, multi-condition AND logic
e.g., "IF tenant=enterprise AND prompt contains 'code' → route to GPT-4"

✅ A/B Testing Framework
Deterministic hash-based variant assignment, traffic-weighted splitting
Per-variant metrics: success rate, latency, cost comparison

✅ Observability
Prometheus metrics export with per-provider and per-model breakdowns

📊 Impact
304 tests passing. 0 type errors. 0 linting errors.
Production-ready infrastructure for any team routing across Azure OpenAI and OpenAI.

GitHub: https://github.com/syabdulr/Azure-AI-Infrastructure-Platform

#AIPlatformEngineering #AzureOpenAI #AgenticAI #SoftwareEngineering #Python"""

print("\nSending draft post...")
text_resp = requests.post(
    f"{BASE}/sendMessage",
    json={
        "chat_id": chat_id,
        "text": draft_post,
    }
)
print(f"Text: {text_resp.status_code}")

if photo_resp.status_code == 200 and text_resp.status_code == 200:
    print("\n✅ Visual + draft post sent to LinkedInProfMediaAgent!")
else:
    print(f"\n❌ Something failed. Photo: {photo_resp.status_code}, Text: {text_resp.status_code}")
