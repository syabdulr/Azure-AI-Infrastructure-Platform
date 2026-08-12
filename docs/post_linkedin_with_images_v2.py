#!/usr/bin/env python3
"""
Post to LinkedIn with images (Budget Enforcement) - Fixed version
"""

import json
import requests

# Load credentials
with open('/home/openclaw/linkedin_credentials.json', 'r') as f:
    creds = json.load(f)

access_token = creds['access_token']
user_id = creds['user_id']

# Image paths
terminal_image = '/tmp/budget_demo_screenshot.png'
flowchart_image = '/tmp/budget_flowchart.png'

# Register terminal image
print("Registering terminal image...")
response1 = requests.post(
    "https://api.linkedin.com/v2/assets?action=registerUpload",
    headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    },
    json={
        "registerUploadRequest": {
            "owner": f"urn:li:person:{user_id}",
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "serviceRelationships": [
                {
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent"
                }
            ]
        }
    }
)

print(f"Registration status code: {response1.status_code}")

if response1.status_code not in [200, 201]:
    print(f"Failed to register terminal image: {response1.text}")
    exit(1)

asset1_data = response1.json()
upload_url1 = asset1_data['value']['uploadMechanism']["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]['uploadUrl']
asset1_urn = asset1_data['value']['asset']

print(f"Asset URN: {asset1_urn}")

# Upload terminal image
print("Uploading terminal image...")
with open(terminal_image, 'rb') as f:
    upload_response1 = requests.put(upload_url1, data=f, headers={})

if upload_response1.status_code not in [200, 201]:
    print(f"Failed to upload terminal image: {upload_response1.text}")
    exit(1)

print(f"✓ Terminal image uploaded")

# Register flowchart image
print("Registering flowchart image...")
response2 = requests.post(
    "https://api.linkedin.com/v2/assets?action=registerUpload",
    headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    },
    json={
        "registerUploadRequest": {
            "owner": f"urn:li:person:{user_id}",
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "serviceRelationships": [
                {
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent"
                }
            ]
        }
    }
)

print(f"Registration status code: {response2.status_code}")

if response2.status_code not in [200, 201]:
    print(f"Failed to register flowchart image: {response2.text}")
    exit(1)

asset2_data = response2.json()
upload_url2 = asset2_data['value']['uploadMechanism']["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]['uploadUrl']
asset2_urn = asset2_data['value']['asset']

print(f"Asset URN: {asset2_urn}")

# Upload flowchart image
print("Uploading flowchart image...")
with open(flowchart_image, 'rb') as f:
    upload_response2 = requests.put(upload_url2, data=f, headers={})

if upload_response2.status_code not in [200, 201]:
    print(f"Failed to upload flowchart image: {upload_response2.text}")
    exit(1)

print(f"✓ Flowchart image uploaded")

# LinkedIn post content
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
✅ Real-Time Cost Tracking
✅ Intelligent Alerting (80%, 90%, 100% thresholds)
✅ Automatic Throttling when budget exceeded

🔧 Technical Implementation

Built with Python using dataclasses and threading:
- BudgetConfig: Provider-specific budget configuration
- BudgetUsage: Daily/monthly tracking with reset logic
- BudgetManager: Orchestration with thread-safe operations
- Alert callbacks: External notification hooks

Tested with 29 unit tests (100% pass rate).

📊 Demo Output (see images):

The terminal screenshot shows the system in action:
- 80% alert threshold (yellow warning)
- 90% critical warning (orange)
- 100% budget exceeded (red alert)
- Automatic request blocking
- Budget reset & recovery

The flowchart visualizes the complete budget enforcement architecture:
- API Request -> Budget Check -> Cost Tracking
- Threshold Detection -> Alerting -> Throttling
- Report Generation

📊 Impact

Combined with the multi-provider caching system I built earlier:
- 30-40% cost reduction from caching
- 100% cost control from budget enforcement
- Real-time visibility into spending
- Automatic safeguards against overspending

🚀 This is production-ready infrastructure for any team using multiple AI providers.

GitHub: https://github.com/syabdulr/Azure-AI-Infrastructure-Platform

#AIPlatformEngineering #DevOps #CloudArchitecture #CostOptimization #Python"""

# Create post with images
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
                "shareMediaCategory": "IMAGE",
                "media": [
                    {
                        "status": "READY",
                        "description": {
                            "text": "Budget Enforcement Demo - Terminal Output"
                        },
                        "media": asset1_urn,
                        "title": {
                            "text": "Terminal Demo"
                        }
                    },
                    {
                        "status": "READY",
                        "description": {
                            "text": "Budget Enforcement Flowchart - Architecture"
                        },
                        "media": asset2_urn,
                        "title": {
                            "text": "System Flowchart"
                        }
                    }
                ]
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
)

print(f"Post creation status code: {post_response.status_code}")

if post_response.status_code == 201:
    result = post_response.json()
    post_id = result['id']
    post_url = f"https://www.linkedin.com/feed/update/urn:li:share:{post_id.split(':')[-1]}"
    print(f"\n✅ LinkedIn post published successfully!")
    print(f"Post ID: {post_id}")
    print(f"URL: {post_url}")
    print(f"\nImages uploaded:")
    print(f"  1. Terminal Demo: {asset1_urn}")
    print(f"  2. Flowchart: {asset2_urn}")
else:
    print(f"❌ Failed to publish: {post_response.status_code}")
    print(f"Response: {post_response.text}")