"""Post flowchart as LinkedIn follow-up."""

import json
import requests

# Load credentials
with open("/home/openclaw/linkedin_credentials.json", "r") as f:
    linkedin_creds = json.load(f)

ACCESS_TOKEN = linkedin_creds["access_token"]
USER_ID = linkedin_creds["user_id"]

# Follow-up post text
POST_TEXT = """Visual representation of the Multi-Provider AI Gateway architecture:

Key components shown:
• Client Application
• Provider Registry with 4 routing strategies
• Health Checks & Circuit Breaker
• Auto-Failover mechanism
• Response Normalization
• Metric Collection

This architecture prevents single points of failure and ensures high availability for production AI systems.

#AIInfrastructure #SystemArchitecture #DevOps #CloudResilience"""

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

    print("📤 Registering upload...")
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

    print("📤 Uploading image...")
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
                        "description": {"text": "Multi-Provider AI Gateway Architecture Flowchart"},
                        "media": asset_urn,
                        "title": {"text": "Architecture Flowchart"}
                    }
                ]
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    print("📝 Creating post with image...")
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
    print("🚀 Posting Flowchart to LinkedIn")
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
    print("✅ Flowchart post live!")
    print(f"✅ View: {post_url}")
    print("=" * 50)

if __name__ == "__main__":
    main()