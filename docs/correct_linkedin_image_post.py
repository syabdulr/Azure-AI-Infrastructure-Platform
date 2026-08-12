"""
Correct LinkedIn image post workflow - v2 Assets API (NO version header)

Based on linkedin-content-management skill:
- Use /v2/assets endpoint (NOT /rest/assets or /rest/images)
- NO LinkedIn-Version header required
- PUT binary upload without Content-Type
- Post via /v2/ugcPosts with asset URN
"""

import json
import requests
import base64

# Load credentials
with open("/home/openclaw/linkedin_credentials.json", "r") as f:
    linkedin_creds = json.load(f)

ACCESS_TOKEN = linkedin_creds["access_token"]
USER_ID = linkedin_creds["user_id"]

# Post content
POST_TEXT = """Building AI systems that don't rely on a single vendor is critical for production resilience.

Single points of failure in AI infrastructure are unacceptable for production systems. If your provider goes down, you lose all AI capabilities.

I've built a multi-provider AI gateway that routes requests across Azure OpenAI and OpenAI with intelligent failover and multiple routing strategies.

Key Features:

• 4 routing strategies: round-robin, cost-optimized, performance-based, health-based
• Circuit breaker pattern prevents cascading failures
• Health monitoring with 30-second intervals
• Automatic failover between providers
• 38 passing tests, 10% code coverage

Impact:

✅ Automatic failover to alternate providers
✅ Circuit breaker pattern prevents cascading failures
✅ 4 routing strategies
✅ Health monitoring with 30-second intervals
✅ Full metrics collection per provider
✅ 38 passing tests, 10% code coverage

GitHub: https://github.com/syabdulr/Azure-AI-Infrastructure-Platform

Building resilient AI infrastructure prevents vendor lock-in and ensures high availability. The multi-provider gateway architecture doesn't just route requests—it builds production-grade systems that handle failures gracefully.

#AIInfrastructure #MultiProvider #CloudResilience #ProductionAI #DevOps #Azure #OpenAI #LLMOps #SystemArchitecture"""

# Flowchart image path
IMAGE_PATH = "/home/openclaw/azure-ai-infra-platform/docs/flowchart.png"

def register_upload():
    """Register image upload via v2 Assets API (NO version header)."""
    register_url = "https://api.linkedin.com/v2/assets?action=registerUpload"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
        # NO LinkedIn-Version header required!
    }

    payload = {
        "registerUploadRequest": {
            "owner": f"urn:li:person:{USER_ID}",
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "serviceRelationships": [
                {
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent"
                }
            ],
            "supportedUploadMechanism": ["SYNCHRONOUS_UPLOAD"]
        }
    }

    print("📤 Step 1: Registering upload via v2 Assets API...")
    response = requests.post(register_url, headers=headers, json=payload)

    if not response.ok:
        print(f"❌ Failed: {response.status_code}")
        print(f"❌ Error: {response.text}")
        return None, None

    register_data = response.json()

    try:
        upload_url = register_data["value"]["uploadMechanism"][
            "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
        ]["uploadUrl"]
        asset_urn = register_data["value"]["asset"]
        print(f"✅ Asset URN: {asset_urn}")
        return upload_url, asset_urn
    except KeyError as e:
        print(f"❌ Parse error: {e}")
        print(f"❌ Response: {register_data}")
        return None, None

def upload_image(upload_url):
    """Upload image binary (NO Content-Type header)."""
    print("📤 Step 2: Uploading image binary...")

    # Read image as binary
    with open(IMAGE_PATH, "rb") as f:
        image_data = f.read()

    # PUT upload (NO Content-Type header!)
    upload_headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "X-Restli-Protocol-Version": "2.0.0"
    }

    response = requests.put(upload_url, headers=upload_headers, data=image_data)

    if not response.ok:
        print(f"❌ Failed: {response.status_code}")
        print(f"❌ Error: {response.text}")
        return False

    print("✅ Image uploaded (201 Created)")
    return True

def create_post(asset_urn):
    """Create LinkedIn post with image via v2 UGC Posts API."""
    create_url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }

    payload = {
        "author": f"urn:li:person:{USER_ID}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": POST_TEXT},
                "shareMediaCategory": "IMAGE",
                "media": [
                    {
                        "status": "READY",
                        "description": {
                            "text": "Multi-Provider AI Gateway Architecture - showing client request routing through provider registry with 4 strategies, health checks, circuit breaker pattern, and automatic failover between Azure OpenAI and OpenAI providers"
                        },
                        "media": asset_urn,
                        "title": {
                            "text": "Multi-Provider AI Gateway Architecture"
                        }
                    }
                ]
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    print("📝 Step 3: Creating post with image...")
    response = requests.post(create_url, headers=headers, json=payload)

    if not response.ok:
        print(f"❌ Failed: {response.status_code}")
        print(f"❌ Error: {response.text}")
        return None

    post_data = response.json()

    try:
        post_urn = post_data["id"]
        post_url = f"https://www.linkedin.com/feed/update/{post_urn.replace(':', '/')}"
        print(f"✅ Post URN: {post_urn}")
        return post_url
    except KeyError as e:
        print(f"❌ Parse error: {e}")
        print(f"❌ Response: {post_data}")
        return None

def main():
    print("🚀 LinkedIn Image Post (Correct v2 Workflow)")
    print("=" * 60)
    print()

    # Step 1: Register upload
    upload_url, asset_urn = register_upload()
    if not upload_url or not asset_urn:
        print("❌ Failed to register upload")
        return

    # Step 2: Upload image
    if not upload_image(upload_url):
        print("❌ Failed to upload image")
        return

    # Step 3: Create post
    post_url = create_post(asset_urn)
    if not post_url:
        print("❌ Failed to create post")
        return

    print()
    print("=" * 60)
    print("✅ Post with flowchart image live!")
    print(f"✅ View: {post_url}")
    print("=" * 60)

if __name__ == "__main__":
    main()