"""Create new LinkedIn post with full content + flowchart image."""

import json
import requests

# Load credentials
with open("/home/openclaw/linkedin_credentials.json", "r") as f:
    linkedin_creds = json.load(f)

ACCESS_TOKEN = linkedin_creds["access_token"]
USER_ID = linkedin_creds["user_id"]

# Full post content
POST_TEXT = """Building AI systems that don't rely on a single vendor is critical for production resilience.

Single points of failure in AI infrastructure are unacceptable for production systems. If your provider goes down, you lose all AI capabilities.

I've built a multi-provider AI gateway that routes requests across Azure OpenAI and OpenAI with intelligent failover and multiple routing strategies.

Architecture shown in the image:

Client → Provider Registry → Routing Strategy → Health Check → Provider API
                                           ↓
                                   Circuit Breaker
                                           ↓
                                   Auto-Failover

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
    """Register image upload with LinkedIn Assets API."""
    url = "https://api.linkedin.com/rest/assets?action=registerUpload"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": "202401"
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

    print("📤 Step 1: Registering upload...")
    response = requests.post(url, headers=headers, json=payload)

    if not response.ok:
        print(f"❌ Failed: {response.status_code}")
        print(f"❌ Error: {response.text}")
        return None, None

    data = response.json()

    try:
        upload_url = data["value"]["uploadMechanism"][
            "com.linkedin.digitalmedia.uploading.MediaUploadHTTPRequest"
        ]["uploadUrl"]
        asset_urn = data["value"]["asset"]
        print(f"✅ Asset URN: {asset_urn}")
        return upload_url, asset_urn
    except KeyError as e:
        print(f"❌ Parse error: {e}")
        return None, None

def upload_image(upload_url):
    """Upload image to LinkedIn."""
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": "202401"
    }

    print("📤 Step 2: Uploading image...")
    with open(IMAGE_PATH, "rb") as f:
        image_data = f.read()

    response = requests.put(upload_url, headers=headers, data=image_data)

    if not response.ok:
        print(f"❌ Failed: {response.status_code}")
        print(f"❌ Error: {response.text}")
        return False

    print("✅ Image uploaded")
    return True

def create_post(asset_urn):
    """Create LinkedIn post with image."""
    url = "https://api.linkedin.com/rest/ugcPosts"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": "202401"
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
                        "description": {"text": "Multi-Provider AI Gateway Architecture Flowchart - showing client request routing through provider registry with health checks, circuit breaker pattern, and automatic failover to alternate providers"},
                        "media": asset_urn,
                        "title": {"text": "Multi-Provider AI Gateway Architecture"}
                    }
                ]
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    print("📝 Step 3: Creating post with image...")
    response = requests.post(url, headers=headers, json=payload)

    if not response.ok:
        print(f"❌ Failed: {response.status_code}")
        print(f"❌ Error: {response.text}")
        return None

    data = response.json()

    try:
        post_urn = data["id"]
        post_url = f"https://www.linkedin.com/feed/update/{post_urn.replace(':', '/')}"
        print(f"✅ Post URN: {post_urn}")
        return post_url
    except KeyError as e:
        print(f"❌ Parse error: {e}")
        return None

def main():
    print("🚀 LinkedIn Post with Flowchart Image")
    print("=" * 50)

    upload_url, asset_urn = register_upload()
    if not upload_url or not asset_urn:
        print("❌ Failed to register upload")
        return

    if not upload_image(upload_url):
        print("❌ Failed to upload image")
        return

    post_url = create_post(asset_urn)
    if not post_url:
        print("❌ Failed to create post")
        return

    print()
    print("=" * 50)
    print("✅ Post with flowchart live!")
    print(f"✅ View: {post_url}")
    print("=" * 50)

if __name__ == "__main__":
    main()