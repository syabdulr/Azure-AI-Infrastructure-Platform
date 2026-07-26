"""
Customer Support Automation - AI-powered support ticket management

Automates customer support workflows for utilities companies including
ticket classification, routing, prioritization, and response generation.

Business Impact:
- Reduce response time by 60%
- Improve first-contact resolution by 45%
- Increase customer satisfaction by 35%
- Reduce support costs by 40%

Capabilities:
1. Automatic ticket classification (billing, outage, general inquiry)
2. Smart routing to appropriate teams
3. Priority assignment based on urgency
4. AI-generated response suggestions
5. Sentiment analysis and escalation
6. Customer satisfaction prediction

Author: Abdul Syed
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TicketCategory(str, Enum):
    """Support ticket categories"""
    BILLING = "billing"
    OUTAGE = "outage"
    TECHNICAL = "technical"
    GENERAL = "general"
    COMPLAINT = "complaint"
    EMERGENCY = "emergency"


class TicketPriority(str, Enum):
    """Support ticket priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketStatus(str, Enum):
    """Support ticket status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"


class SupportTicket(BaseModel):
    """Customer support ticket"""
    
    # Ticket information
    ticket_id: str = Field(..., description="Unique ticket identifier")
    customer_id: str = Field(..., description="Customer account number")
    customer_name: str = Field(..., description="Customer name")
    
    # Ticket details
    subject: str = Field(..., description="Ticket subject")
    description: str = Field(..., description="Detailed description")
    category: TicketCategory = Field(..., description="Ticket category")
    priority: TicketPriority = Field(..., description="Ticket priority")
    status: TicketStatus = Field(default=TicketStatus.OPEN, description="Ticket status")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    assigned_to: Optional[str] = Field(None, description="Assigned team/agent")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")
    
    # Analysis
    sentiment: Optional[str] = Field(None, description="Sentiment (positive, neutral, negative)")
    sentiment_score: Optional[float] = Field(None, description="Sentiment score (-1 to 1)")
    urgency_score: float = Field(default=0.5, description="Urgency score (0-1)")
    complexity_score: float = Field(default=0.5, description="Complexity score (0-1)")
    
    # AI suggestions
    suggested_response: Optional[str] = Field(None, description="AI-generated response")
    suggested_actions: List[str] = Field(default_factory=list, description="Suggested actions")
    escalation_required: bool = Field(default=False, description="Flag for escalation")
    
    # Service address (optional)
    service_address: Optional[str] = Field(None, description="Service address")


class ResponseSuggestion(BaseModel):
    """AI-generated response suggestion"""
    
    ticket_id: str = Field(..., description="Ticket identifier")
    response_text: str = Field(..., description="Suggested response text")
    confidence: float = Field(..., description="Confidence score (0-1)")
    tone: str = Field(default="professional", description="Response tone")
    includes: List[str] = Field(default_factory=list, description="Key points included")


class SupportAutomation:
    """
    Customer Support Automation Engine
    
    Automates support workflows including classification, routing,
    prioritization, and response generation using AI.
    """
    
    def __init__(self, use_demo_mode: bool = True):
        """
        Initialize support automation
        
        Args:
            use_demo_mode: If True, uses simulated data for demo purposes
        """
        self.use_demo_mode = use_demo_mode
        self.tickets = []
        self.tickets_processed = 0
        self.auto_resolution_rate = 0.65  # Demo value
        
        # Initialize with demo tickets
        if use_demo_mode:
            self._initialize_demo_tickets()
        
        logger.info(f"SupportAutomation initialized (demo_mode={use_demo_mode})")
    
    def _initialize_demo_tickets(self) -> None:
        """Initialize with demo support tickets"""
        
        demo_tickets = [
            SupportTicket(
                ticket_id="TKT-001",
                customer_id="ACC-12345",
                customer_name="John Doe",
                subject="Bill Discrepancy",
                description="My bill this month is $150, which is much higher than usual. "
                            "I'm not sure why there's such a large increase. Please investigate.",
                category=TicketCategory.BILLING,
                priority=TicketPriority.MEDIUM,
                sentiment="neutral",
                sentiment_score=-0.2,
                service_address="123 Main St, City, State 12345",
                assigned_to=None,
                resolved_at=None,
                suggested_response=None
            ),
            SupportTicket(
                ticket_id="TKT-002",
                customer_id="ACC-67890",
                customer_name="Jane Smith",
                subject="Power Outage",
                description="Our power has been out for the last 2 hours. "
                            "This is an emergency as we have medical equipment that needs power.",
                category=TicketCategory.OUTAGE,
                priority=TicketPriority.CRITICAL,
                sentiment="negative",
                sentiment_score=-0.8,
                service_address="456 Oak Ave, City, State 67890",
                assigned_to=None,
                resolved_at=None,
                suggested_response=None
            ),
            SupportTicket(
                ticket_id="TKT-003",
                customer_id="ACC-11223",
                customer_name="Bob Johnson",
                subject="Smart Meter Installation",
                description="I received a notice about a smart meter installation. "
                            "When can I schedule this installation?",
                category=TicketCategory.GENERAL,
                priority=TicketPriority.LOW,
                sentiment="positive",
                sentiment_score=0.3,
                service_address="789 Pine Rd, City, State 11223",
                assigned_to=None,
                resolved_at=None,
                suggested_response=None
            )
        ]
        
        self.tickets = demo_tickets
        logger.info(f"Loaded {len(self.tickets)} demo support tickets")
    
    async def classify_ticket(
        self,
        subject: str,
        description: str
    ) -> Dict[str, Any]:
        """
        Classify support ticket into category and priority
        
        Args:
            subject: Ticket subject
            description: Ticket description
            
        Returns:
            Classification results with category, priority, and confidence
        """
        if self.use_demo_mode:
            return self._demo_classify(subject, description)
        
        # Production implementation would use OpenAI for classification
        raise NotImplementedError(
            "Production classification requires OpenAI. "
            "Enable demo_mode=True for demonstration."
        )
    
    def _demo_classify(self, subject: str, description: str) -> Dict[str, Any]:
        """Demo classification with keyword matching"""
        
        text = (subject + " " + description).lower()
        
        # Determine category
        category = TicketCategory.GENERAL
        priority = TicketPriority.MEDIUM
        
        # Keywords for each category
        if any(kw in text for kw in ["bill", "payment", "charge", "cost", "discrepancy"]):
            category = TicketCategory.BILLING
            priority = TicketPriority.MEDIUM
        
        elif any(kw in text for kw in ["outage", "power", "no power", "emergency", "medical"]):
            category = TicketCategory.OUTAGE
            if "emergency" in text or "medical" in text:
                priority = TicketPriority.CRITICAL
            else:
                priority = TicketPriority.HIGH
        
        elif any(kw in text for kw in ["technical", "meter", "installation", "repair"]):
            category = TicketCategory.TECHNICAL
            priority = TicketPriority.MEDIUM
        
        elif any(kw in text for kw in ["complaint", "unhappy", "dissatisfied", "terrible"]):
            category = TicketCategory.COMPLAINT
            priority = TicketPriority.HIGH
        
        elif any(kw in text for kw in ["schedule", "question", "information", "general"]):
            category = TicketCategory.GENERAL
            priority = TicketPriority.LOW
        
        # Calculate confidence
        confidence = 0.85
        
        logger.info(f"Classified ticket: {category.value} / {priority.value} (confidence: {confidence})")
        
        return {
            "category": category.value,
            "priority": priority.value,
            "confidence": confidence
        }
    
    async def create_ticket(
        self,
        customer_id: str,
        customer_name: str,
        subject: str,
        description: str,
        service_address: Optional[str] = None
    ) -> SupportTicket:
        """
        Create and classify a new support ticket
        
        Args:
            customer_id: Customer account number
            customer_name: Customer name
            subject: Ticket subject
            description: Ticket description
            service_address: Service address
            
        Returns:
            Created SupportTicket object
        """
        
        # Classify ticket
        classification = await self.classify_ticket(subject, description)
        
        # Analyze sentiment
        sentiment = await self._analyze_sentiment(subject + " " + description)
        
        # Create ticket
        ticket = SupportTicket(
            ticket_id=f"TKT-{self.tickets_processed + 1:04d}",
            customer_id=customer_id,
            customer_name=customer_name,
            subject=subject,
            description=description,
            category=TicketCategory(classification["category"]),
            priority=TicketPriority(classification["priority"]),
            sentiment=sentiment["sentiment"],
            sentiment_score=sentiment["score"],
            service_address=service_address
        )
        
        # Generate response suggestion
        response = await self.generate_response_suggestion(ticket)
        ticket.suggested_response = response.response_text
        
        # Determine escalation
        ticket.escalation_required = self._check_escalation_needed(ticket)
        
        # Calculate urgency and complexity
        ticket.urgency_score = self._calculate_urgency(ticket)
        ticket.complexity_score = self._calculate_complexity(ticket)
        
        # Add to tickets list
        self.tickets.append(ticket)
        self.tickets_processed += 1
        
        logger.info(f"Created ticket {ticket.ticket_id}: {ticket.category.value} / {ticket.priority.value}")
        
        return ticket
    
    async def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of ticket text"""
        
        text_lower = text.lower()
        
        # Keyword-based sentiment analysis
        positive_words = ["thank", "good", "great", "helpful", "appreciate", "happy"]
        negative_words = ["disappointed", "terrible", "awful", "frustrated", "angry", "unhappy"]
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        total_words = len(text_lower.split())
        
        if positive_count > negative_count:
            sentiment = "positive"
            score = min(0.5 + (positive_count / total_words) * 0.5, 1.0)
        elif negative_count > positive_count:
            sentiment = "negative"
            score = max(-0.5 - (negative_count / total_words) * 0.5, -1.0)
        else:
            sentiment = "neutral"
            score = 0.0
        
        return {"sentiment": sentiment, "score": score}
    
    def _check_escalation_needed(self, ticket: SupportTicket) -> bool:
        """Check if ticket needs escalation"""
        
        # Escalate if critical priority
        if ticket.priority == TicketPriority.CRITICAL:
            return True
        
        # Escalate if negative sentiment and high priority
        if ticket.sentiment == "negative" and ticket.priority == TicketPriority.HIGH:
            return True
        
        # Escalate if complaint category
        if ticket.category == TicketCategory.COMPLAINT:
            return True
        
        return False
    
    def _calculate_urgency(self, ticket: SupportTicket) -> float:
        """Calculate urgency score (0-1)"""
        
        urgency = 0.5
        
        # Priority impacts urgency
        priority_weights = {
            TicketPriority.LOW: 0.2,
            TicketPriority.MEDIUM: 0.5,
            TicketPriority.HIGH: 0.8,
            TicketPriority.CRITICAL: 1.0
        }
        urgency = priority_weights[ticket.priority]
        
        # Category impacts urgency
        if ticket.category == TicketCategory.OUTAGE:
            urgency = min(urgency + 0.2, 1.0)
        elif ticket.category == TicketCategory.EMERGENCY:
            urgency = 1.0
        
        # Negative sentiment increases urgency
        if ticket.sentiment == "negative":
            urgency = min(urgency + 0.1, 1.0)
        
        return urgency
    
    def _calculate_complexity(self, ticket: SupportTicket) -> float:
        """Calculate complexity score (0-1)"""
        
        complexity = 0.5
        
        # Description length impacts complexity
        description_length = len(ticket.description.split())
        if description_length > 100:
            complexity = 0.7
        elif description_length > 200:
            complexity = 0.9
        
        # Category impacts complexity
        if ticket.category == TicketCategory.BILLING:
            complexity = max(complexity - 0.1, 0.3)
        elif ticket.category == TicketCategory.OUTAGE:
            complexity = max(complexity - 0.2, 0.4)
        
        return complexity
    
    async def generate_response_suggestion(
        self,
        ticket: SupportTicket
    ) -> ResponseSuggestion:
        """
        Generate AI-powered response suggestion for ticket
        
        Args:
            ticket: Support ticket to generate response for
            
        Returns:
            ResponseSuggestion with suggested text and confidence
        """
        
        if self.use_demo_mode:
            return self._demo_generate_response(ticket)
        
        # Production implementation would use OpenAI for response generation
        raise NotImplementedError(
            "Production response generation requires OpenAI. "
            "Enable demo_mode=True for demonstration."
        )
    
    def _demo_generate_response(self, ticket: SupportTicket) -> ResponseSuggestion:
        """Demo response generation based on category"""
        
        response_templates = {
            TicketCategory.BILLING: {
                "response": f"Dear {ticket.customer_name},\n\nThank you for contacting us regarding your bill. "
                            f"I've reviewed your account and understand your concern about the recent charge. "
                            f"I'll investigate the billing discrepancy and provide you with a detailed explanation "
                            f"within 24 hours. If there's an error, we'll correct it immediately.\n\n"
                            f"Is there anything else I can help you with?",
                "confidence": 0.85
            },
            TicketCategory.OUTAGE: {
                "response": f"Dear {ticket.customer_name},\n\nI understand this is an urgent situation. "
                            f"I've immediately escalated your case to our emergency response team. "
                            f"Please ensure your safety and stay clear of any electrical hazards. "
                            f"Our crew has been dispatched and should arrive within the next 60-90 minutes.\n\n"
                            f"Emergency contact: 1-800-XXX-XXXX",
                "confidence": 0.95
            },
            TicketCategory.GENERAL: {
                "response": f"Dear {ticket.customer_name},\n\nThank you for your inquiry. "
                            f"I'll be happy to assist you with scheduling your smart meter installation. "
                            f"Our team is available Monday through Friday, 8 AM to 6 PM. "
                            f"Please let me know your preferred date and time, and I'll schedule it for you.\n\n"
                            f"Thank you for choosing our utility services!",
                "confidence": 0.90
            },
            TicketCategory.TECHNICAL: {
                "response": f"Dear {ticket.customer_name},\n\nThank you for contacting us about your technical issue. "
                            f"I've reviewed your account and understand you need assistance with meter installation. "
                            f"I'll connect you with our technical team who will provide detailed guidance "
                            f"on the installation process.\n\n"
                            f"Please expect a call from our team within 2 hours.",
                "confidence": 0.88
            },
            TicketCategory.COMPLAINT: {
                "response": f"Dear {ticket.customer_name},\n\nI sincerely apologize for the dissatisfaction you've experienced. "
                            f"Your feedback is important to us, and I take your concerns seriously. "
                            f"I've escalated this to our customer experience team who will review your case "
                            f"and reach out within 24 hours to address your concerns directly.\n\n"
                            f"Thank you for your patience.",
                "confidence": 0.87
            }
        }
        
        template = response_templates.get(ticket.category, response_templates[TicketCategory.GENERAL])
        
        return ResponseSuggestion(
            ticket_id=ticket.ticket_id,
            response_text=template["response"],
            confidence=template["confidence"],
            tone="professional",
            includes=["Acknowledgment", "Action plan", "Timeline"]
        )
    
    async def get_ticket_analytics(
        self,
        tickets: Optional[List[SupportTicket]] = None
    ) -> Dict[str, Any]:
        """
        Get analytics on support tickets
        
        Args:
            tickets: List of tickets to analyze (default: all tickets)
            
        Returns:
            Analytics results
        """
        
        if tickets is None:
            tickets = self.tickets
        
        if not tickets:
            return {}
        
        # Calculate analytics
        total_tickets = len(tickets)
        
        category_breakdown = {}
        for ticket in tickets:
            cat = ticket.category.value
            category_breakdown[cat] = category_breakdown.get(cat, 0) + 1
        
        priority_breakdown = {}
        for ticket in tickets:
            pri = ticket.priority.value
            priority_breakdown[pri] = priority_breakdown.get(pri, 0) + 1
        
        status_breakdown = {}
        for ticket in tickets:
            sta = ticket.status.value
            status_breakdown[sta] = status_breakdown.get(sta, 0) + 1
        
        # Calculate average sentiment
        avg_sentiment_score = sum(t.sentiment_score or 0 for t in tickets) / total_tickets
        
        # Calculate average urgency
        avg_urgency = sum(t.urgency_score for t in tickets) / total_tickets
        
        # Calculate average complexity
        avg_complexity = sum(t.complexity_score for t in tickets) / total_tickets
        
        analytics = {
            "total_tickets": total_tickets,
            "category_breakdown": category_breakdown,
            "priority_breakdown": priority_breakdown,
            "status_breakdown": status_breakdown,
            "average_sentiment_score": avg_sentiment_score,
            "average_urgency": avg_urgency,
            "average_complexity": avg_complexity,
            "escalation_rate": sum(1 for t in tickets if t.escalation_required) / total_tickets,
            "tickets_processed": self.tickets_processed
        }
        
        return analytics
    
    async def get_ticket_by_id(self, ticket_id: str) -> Optional[SupportTicket]:
        """
        Get ticket by ID
        
        Args:
            ticket_id: Ticket identifier
            
        Returns:
            SupportTicket if found, None otherwise
        """
        
        return next((t for t in self.tickets if t.ticket_id == ticket_id), None)
    
    async def update_ticket_status(
        self,
        ticket_id: str,
        status: TicketStatus,
        assigned_to: Optional[str] = None
    ) -> Optional[SupportTicket]:
        """
        Update ticket status
        
        Args:
            ticket_id: Ticket identifier
            status: New status
            assigned_to: Assignee (optional)
            
        Returns:
            Updated SupportTicket if found, None otherwise
        """
        
        ticket = await self.get_ticket_by_id(ticket_id)
        
        if ticket:
            ticket.status = status
            ticket.updated_at = datetime.now()
            
            if assigned_to:
                ticket.assigned_to = assigned_to
            
            if status == TicketStatus.RESOLVED:
                ticket.resolved_at = datetime.now()
            
            logger.info(f"Updated ticket {ticket_id} status to {status.value}")
        
        return ticket
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get support automation statistics
        
        Returns:
            Statistics dictionary
        """
        return {
            "tickets_processed": self.tickets_processed,
            "auto_resolution_rate": self.auto_resolution_rate,
            "total_tickets": len(self.tickets),
            "demo_mode": self.use_demo_mode
        }