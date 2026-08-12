#!/usr/bin/env python3
"""
Post to LinkedIn - Custom Routing Rules + A/B Testing Framework
"""

import json
import requests

# Load credentials
with open('/home/openclaw/linkedin_credentials.json', 'r') as f:
    creds = json.load(f)

access_token = creds['access_token']
user_id = creds['user_id']

post_text = """Shipped 2 new features for my Multi-Provider AI Gateway: Custom Routing Rules + A/B Testing Framework

🎯 The Problem
When routing requests across multiple AI providers, you need two things:
1. Fine-grained control over WHERE requests go (not just "cheapest" or "fastest")
2. Data-driven confidence that your routing decisions are actually correct

💡 The Solution

Feature 1: Custom Routing Rules Engine
✅ 9 operators (equals, contains, in, has_capability, greater_than, etc.)
✅ 4 priority levels (CRITICAL → LOW) with confidence scoring
✅ Multi-condition AND logic — e.g., "IF tenant=enterprise AND prompt contains 'code' → route to GPT-4"
✅ Dynamic rule management — add/remove/enable/disable at runtime
✅ Catch-all fallback rules for sensible defaults

Feature 2: A/B Testing Framework
✅ Experiment lifecycle (draft → running → paused → completed)
✅ Deterministic hash-based variant assignment (same user = same variant every time)
✅ Traffic-weighted splitting (70/30, 50/50 — validated with 1000 requests)
✅ Per-variant metrics: success rate, avg latency, avg cost per request
✅ Results summary comparing control vs treatment across all dimensions

🔧 Technical Implementation

Built with Python:
- Rule engine with priority-ordered evaluation and 9 condition operators
- A/B engine using MD5 hashing for deterministic, reproducible assignments
- Thread-safe operations with reentrant locks
- 66 new tests (31 routing + 35 A/B), full mypy type checking, 0 errors

📊 Impact

Phase 2 is now 83% complete (5/6 features):
✅ Response Normalization
✅ Multi-Provider Caching (30-40% cost reduction)
✅ Budget Enforcement (100% cost control)
✅ Custom Routing Rules (THIS POST)
✅ A/B Testing Framework (THIS POST)
⬜ Observability (next)

279 tests passing. Production-ready infrastructure for any team routing across Azure OpenAI, OpenAI, and beyond.

```bash
$ python -m pytest tests/unit/ --no-cov -q
279 passed in 6.49s
```

GitHub: https://github.com/syabdulr/Azure-AI-Infrastructure-Platform

#AIPlatformEngineering #AzureOpenAI #AgenticAI #SoftwareEngineering #Python"""

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
