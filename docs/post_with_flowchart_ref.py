"""Text-only LinkedIn post that references flowchart in GitHub."""

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

Architecture:

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

See the architecture flowchart in the GitHub repository:
https://github.com/syabdulr/Azure-AI-Infrastructure-Platform

Impact:

✅ Automatic failover to alternate providers
✅ Circuit breaker pattern prevents cascading failures
✅ 4 routing strategies
✅ Health monitoring with 30-second intervals
✅ Full metrics collection per provider
✅ 38 passing tests, 10% code coverage

Building resilient AI infrastructure prevents vendor lock-in and ensures high availability. The multi-provider gateway architecture doesn't just route requests—it builds production-grade systems that handle failures gracefully.

#AIInfrastructure #MultiProvider #CloudResilience #ProductionAI #DevOps #Azure #OpenAI #LLMOps #SystemArchitecture"""

def create_post():
    """Create LinkedIn post (text-only)."""
    url = "https://api.linkedin.com/v2/ugcPosts"
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
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    print("📝 Creating post (text-only)...")
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
    print("🚀 LinkedIn Post with Flowchart Reference")
    print("=" * 50)

    post_url = create_post()
    if not post_url:
        print("❌ Failed to create post")
        return

    print()
    print("=" * 50)
    print("✅ Post live (references flowchart in GitHub)!")
    print(f"✅ View: {post_url}")
    print("=" * 50)

if __name__ == "__main__":
    main()