#!/usr/bin/env python3
"""
Post to LinkedIn - exact structure user liked
"""

import json
import requests

# Load credentials
with open('/home/openclaw/linkedin_credentials.json', 'r') as f:
    creds = json.load(f)

access_token = creds['access_token']
user_id = creds['user_id']

# Exact post content user liked
post_text = """Multi-Provider AI Gateway: Budget Enforcement Feature

Just shipped budget enforcement for my Multi-Provider AI Gateway!

🎯 The Problem
Managing costs across multiple AI providers (OpenAI, Azure OpenAI, etc.) was a nightmare.
- No visibility into per-provider spending
- No automatic alerts when budgets exceeded
- Risk of overspending with no safeguards

💡 The Solution
Built a comprehensive budget enforcement system with:

✅ Per-Provider Budget Limits
- Daily & monthly limits per provider
- Configurable thresholds (e.g., $10/day for OpenAI, $5/day for Azure)
- Auto-renewal with automatic daily/monthly resets

✅ Real-Time Cost Tracking
- Per-request cost accumulation
- Usage metrics (requests, costs, percentages)
- Comprehensive reports by provider

✅ Intelligent Alerting
- 80% warning threshold
- 90% critical warning
- 100% budget exceeded alert
- Alert callback system for notifications

✅ Automatic Throttling
- Pause-on-exceed option
- Request blocking when budget exceeded
- Clear messaging on why requests are blocked

🔧 Technical Implementation

Built with Python using dataclasses and threading:
- BudgetConfig: Provider-specific budget configuration
- BudgetUsage: Daily/monthly tracking with reset logic
- BudgetManager: Orchestration with thread-safe operations
- Alert callbacks: External notification hooks

Tested with 29 unit tests (100% pass rate).

📊 Impact

Combined with the multi-provider caching system I built earlier:
- 30-40% cost reduction from caching
- 100% cost control from budget enforcement
- Real-time visibility into spending
- Automatic safeguards against overspending

🚀 This is production-ready infrastructure for any team using multiple AI providers.

GitHub: https://github.com/syabdulr/Azure-AI-Infrastructure-Platform

#AIPlatformEngineering #DevOps #CloudArchitecture #CostOptimization #Python"""

# Create post
print("Creating LinkedIn post...")
post_response = requests.post(
    "https://api.linkedin.com/v2/ugcPosts",
    headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    },
    json={
        "author": f"urn:li:person:{user_id}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": post_text
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
)

if post_response.status_code == 201:
    result = post_response.json()
    post_id = result['id']
    post_url = f"https://www.linkedin.com/feed/update/urn:li:share:{post_id.split(':')[-1]}"
    print(f"\n✅ LinkedIn post published successfully!")
    print(f"Post ID: {post_id}")
    print(f"URL: {post_url}")
else:
    print(f"❌ Failed to publish: {post_response.status_code}")
    print(f"Response: {post_response.text}")