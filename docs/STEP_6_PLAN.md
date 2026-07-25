# Step 6: Guardrails & Safety - Build Plan

## 🎯 Step Overview

**Commit:** `feat: Implement guardrails and safety framework for AI platform`  
**Estimated Time:** 2 hours  
**Goal:** Build production-ready guardrails and safety features for the AI platform

---

## 🏗️ Guardrails & Safety Architecture

```
┌─────────────────┐
│   Input         │
│   Filter        │
│                 │
│  • PII Detection│
│  • Content      │
│    Filtering    │
│  • Input        │
│    Validation   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Output        │
│   Filter        │
│                 │
│  • Safety Checks│
│  • Content      ││
│    Moderation   │
│  • Response     │
│    Validation   │
└─────────────────┘
```

---

## 📋 Files to Create (5 files, ~1,200 lines)

### 1. Create Input Filter
- `src/guardrails/input_filter.py` (New: 250 lines)
  - PII detection (emails, phone numbers, SSN, credit cards)
  - Content filtering (hate speech, violence, profanity)
  - Input validation (length, format, encoding)
  - SQL injection detection
  - XSS detection

### 2. Create Output Filter
- `src/guardrails/output_filter.py` (New: 250 lines)
  - Safety checks
  - Content moderation
  - Response validation
  - PII redaction
  - Hallucination detection

### 3. Create Rate Limiter
- `src/guardrails/rate_limiter.py` (New: 200 lines)
  - Token bucket algorithm
  - User-based limits
  - API endpoint limits
  - Sliding window tracking
  - Distributed support (Redis)

### 4. Create Safety Manager
- `src/guardrails/safety_manager.py` (New: 300 lines)
  - Coordinate input/output filters
  - Manage safety policies
  - Log violations
  - Alert on critical issues
  - Policy configuration

### 5. Create Guardrails Package
- `src/guardrails/__init__.py` (New: 20 lines)
  - Package initialization
  - Export main classes

---

## 🎯 Key Features to Implement

### 1. PII Detection

```python
class PIIDetector:
    """Detect and handle Personally Identifiable Information"""
    
    def __init__(self):
        self.patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            "credit_card": r'\b(?:\d{4}[- ]?){3}\d{4}\b',
            "ip_address": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            "date_of_birth": r'\b(?:0[1-9]|1[0-2])/(?:0[1-9]|[12]\d|3[01])/\d{4}\b'
        }
    
    def detect(self, text: str) -> Dict[str, List[str]]:
        """
        Detect PII in text
        
        Returns:
            Dictionary with PII types and detected values
        """
        pass
    
    def redact(self, text: str, method: str = "mask") -> str:
        """
        Redact PII from text
        
        Methods:
        - mask: Replace with [REDACTED]
        - hash: Replace with hash
        - partial: Show partial (e.g., a***@email.com)
        """
        pass
```

### 2. Content Filtering

```python
class ContentFilter:
    """Filter harmful content"""
    
    def __init__(self):
        # Keywords and patterns for harmful content
        self.hate_speech_patterns = []
        self.violence_patterns = []
        self.profanity_patterns = []
    
    def filter_input(self, text: str) -> Dict[str, Any]:
        """
        Filter input content
        
        Returns:
            Dictionary with:
            - is_safe: bool
            - violations: list of violations
            - severity: low/medium/high
            - filtered_text: str
        """
        pass
    
    def filter_output(self, text: str) -> Dict[str, Any]:
        """
        Filter output content
        
        Returns:
            Dictionary with safety assessment
        """
        pass
```

### 3. Rate Limiting

```python
class RateLimiter:
    """Rate limiter using token bucket algorithm"""
    
    def __init__(
        self,
        tokens_per_minute: int = 60,
        burst_size: int = 10
    ):
        """
        Initialize rate limiter
        
        Args:
            tokens_per_minute: Refill rate
            burst_size: Maximum burst capacity
        """
        self.tokens_per_minute = tokens_per_minute
        self.burst_size = burst_size
        self.buckets = {}  # {user_id: bucket_state}
    
    def check_limit(
        self,
        user_id: str,
        endpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check if request is within rate limits
        
        Returns:
            Dictionary with:
            - allowed: bool
            - remaining_tokens: int
            - retry_after: int (seconds)
        """
        pass
    
    def consume_token(
        self,
        user_id: str,
        tokens: int = 1
    ):
        """
        Consume tokens for a user
        
        Args:
            user_id: User identifier
            tokens: Number of tokens to consume
        """
        pass
```

### 4. Safety Manager

```python
class SafetyManager:
    """Coordinate all safety and guardrail checks"""
    
    def __init__(self):
        self.pii_detector = PIIDetector()
        self.content_filter = ContentFilter()
        self.rate_limiter = RateLimiter()
        self.output_filter = OutputFilter()
    
    def check_input(
        self,
        user_id: str,
        text: str,
        endpoint: str
    ) -> Dict[str, Any]:
        """
        Perform all input safety checks
        
        Returns:
            Dictionary with:
            - is_safe: bool
            - violations: list of violations
            - filtered_text: str
            - rate_limit_ok: bool
        """
        pass
    
    def check_output(
        self,
        user_id: str,
        text: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform all output safety checks
        
        Returns:
            Dictionary with:
            - is_safe: bool
            - violations: list of violations
            - filtered_text: str
            - redacted_pii: list
        """
        pass
    
    def log_violation(
        self,
        violation_type: str,
        user_id: str,
        details: Dict[str, Any],
        severity: str
    ):
        """
        Log a safety violation
        
        Args:
            violation_type: Type of violation
            user_id: User identifier
            details: Violation details
            severity: Severity level (low/medium/high)
        """
        pass
```

---

## 📊 API Enhancements

### Safety Check Middleware

```python
from fastapi import Request, HTTPException

async def safety_middleware(request: Request, call_next):
    """
    Apply safety checks to all requests
    """
    user_id = request.headers.get("X-User-ID", "anonymous")
    
    # Check rate limits
    rate_check = safety_manager.rate_limiter.check_limit(
        user_id=user_id,
        endpoint=request.url.path
    )
    
    if not rate_check["allowed"]:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Retry after {rate_check['retry_after']} seconds"
        )
    
    # Process request
    response = await call_next(request)
    
    return response
```

### New Safety Endpoints

```python
POST /guardrails/check-input
Description: Check input safety

Request:
{
  "text": "User input text",
  "user_id": "user-123"
}

Response:
{
  "is_safe": true,
  "violations": [],
  "filtered_text": "Filtered text",
  "pii_detected": {
    "email": ["user@example.com"]
  },
  "severity": "none"
}
```

```python
POST /guardrails/check-output
Description: Check output safety

Request:
{
  "text": "AI response",
  "user_id": "user-123",
  "context": "Original query"
}

Response:
{
  "is_safe": true,
  "violations": [],
  "filtered_text": "Filtered response",
  "redacted_pii": [],
  "severity": "none"
}
```

```python
GET /guardrails/limits/{user_id}
Description: Get rate limit status for user

Response:
{
  "user_id": "user-123",
  "tokens_per_minute": 60,
  "remaining_tokens": 45,
  "reset_time": "2026-07-25T12:05:00Z",
  "endpoints": {
    "/chat": {"remaining": 15, "limit": 30},
    "/rag/query": {"remaining": 30, "limit": 60}
  }
}
```

```python
GET /guardrails/violations
Description: Get recent safety violations

Query Parameters:
- user_id: Filter by user (optional)
- severity: Filter by severity (optional)
- limit: Number of results (default: 50)

Response:
{
  "violations": [
    {
      "id": "viol-123",
      "type": "pii_detected",
      "user_id": "user-123",
      "severity": "medium",
      "details": {...},
      "timestamp": "2026-07-25T12:00:00Z"
    }
  ],
  "total": 100,
  "count": 50
}
```

---

## 🔒 Safety Features

### 1. PII Detection & Redaction
- Email addresses
- Phone numbers
- Social Security Numbers
- Credit card numbers
- IP addresses
- Dates of birth
- Redaction methods: mask, hash, partial

### 2. Content Filtering
- Hate speech detection
- Violence detection
- Profanity filtering
- Adult content detection
- Spam detection

### 3. Input Validation
- Length limits
- Format validation
- Encoding checks
- SQL injection prevention
- XSS prevention

### 4. Output Safety
- Response validation
- Hallucination detection
- Source verification (for RAG)
- Confidence scoring
- Fact-checking

### 5. Rate Limiting
- Token bucket algorithm
- User-based limits
- Per-endpoint limits
- Burst handling
- Distributed support (Redis)

---

## 💰 Cost Optimization

### 1. Efficient Filtering
- Early rejection of harmful content
- Reduce LLM API calls
- Save token costs

### 2. Rate Limiting
- Prevent abuse
- Control costs
- Fair resource allocation

### 3. Caching
- Cache PII detection results
- Cache content filter results
- Reduce重复 computation

---

## 🧪 Testing Strategy

### Unit Tests
- `test_pii_detector.py`
  - PII detection accuracy
  - Redaction methods
  - Edge cases

- `test_content_filter.py`
  - Content filtering
  - False positives
  - False negatives

- `test_rate_limiter.py`
  - Rate limiting accuracy
  - Token bucket behavior
  - Burst handling

### Integration Tests
- `test_safety_manager.py`
  - End-to-end safety checks
  - Policy enforcement
  - Violation logging

---

## 📝 Success Criteria

✅ PII detection for 6+ types  
✅ Content filtering for 4+ categories  
✅ Rate limiting with token bucket  
✅ Input/output safety middleware  
✅ Safety management API (4+ endpoints)  
✅ Violation logging  
✅ Policy configuration  
✅ Redaction support (3+ methods)  
✅ Distributed rate limiting support  
✅ Unit tests for all components  

---

## 🚀 What This Will Add

**New Functionality:**
- ✅ Complete safety framework
- ✅ PII detection and redaction
- ✅ Content filtering
- ✅ Rate limiting
- ✅ Input/output validation
- ✅ Safety management API

**Recruiter Impact:**
- ✅ Demonstrates enterprise-grade security
- ✅ Shows compliance awareness (GDPR, SOC2)
- ✅ Production-ready safety measures
- ✅ Addresses real-world AI risks
- ✅ Responsible AI implementation

---

## 📊 Progress After Step 6

- **Files Created:** 5 new files (~1,020 lines)
- **Files Updated:** 2 files (~30 lines)
- **Total New Code:** ~1,050 lines
- **Commits:** 6 total
- **Steps Complete:** 6/13 (46.2%)

---

## ⏭️ Ready to Build?

**Next Action:** Implement guardrails and safety framework

**Estimated Time:** 2 hours

**Type "yes" to start building Step 6!** 🚀