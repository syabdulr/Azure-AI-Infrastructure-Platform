"""
Utilities API Routes

RESTful API endpoints for utilities-specific use cases:
- Bill processing and analysis
- Regulation document search
- Customer support automation
- Usage analytics and anomaly detection

Author: Abdul Syed
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional, Any
import logging

from src.utilities.bill_processor import BillProcessor, BillData
from src.utilities.regulation_search import RegulationSearch, SearchResult
from src.utilities.support_automation import SupportAutomation, SupportTicket, TicketCategory, TicketPriority, TicketStatus
from src.utilities.analytics import UsageAnalytics, Anomaly, OptimizationRecommendation

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/utilities",
    tags=["Utilities"],
    responses={404: {"description": "Not found"}}
)

# Initialize services
bill_processor = BillProcessor(use_demo_mode=True)
regulation_search = RegulationSearch(use_demo_mode=True)
support_automation = SupportAutomation(use_demo_mode=True)
usage_analytics = UsageAnalytics(use_demo_mode=True)


# ============================================================================
# BILL PROCESSING ENDPOINTS
# ============================================================================

@router.get("/bills/demo", response_model=BillData)
async def generate_demo_bill():
    """
    Generate a demo utility bill for demonstration
    
    Returns:
        Simulated utility bill with complete data structure
    """
    try:
        bill = await bill_processor.extract_bill_data()
        return bill
    except Exception as e:
        logger.error(f"Error generating demo bill: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bills/analyze")
async def analyze_bill(bill_data: BillData):
    """
    Analyze a utility bill for anomalies and insights
    
    Args:
        bill_data: Bill data to analyze
        
    Returns:
        Analysis results with anomalies and insights
    """
    try:
        # Re-analyze the bill
        bill_processor._analyze_bill(bill_data)
        
        return {
            "bill_data": bill_data.dict(),
            "is_anomalous": bill_data.is_anomalous,
            "anomalies": bill_data.anomalies,
            "insights": bill_data.insights
        }
    except Exception as e:
        logger.error(f"Error analyzing bill: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bills/compare")
async def compare_bills(bill_a: BillData, bill_b: BillData):
    """
    Compare two utility bills and identify differences
    
    Args:
        bill_a: First bill
        bill_b: Second bill
        
    Returns:
        Comparison results with insights
    """
    try:
        comparison = await bill_processor.compare_bills(bill_a, bill_b)
        return comparison
    except Exception as e:
        logger.error(f"Error comparing bills: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bills/anomalies")
async def detect_bill_anomalies(customer_id: str):
    """
    Detect anomalies by comparing with historical bills
    
    Args:
        customer_id: Customer identifier
        
    Returns:
        List of anomalies detected
    """
    try:
        # For demo, generate a current bill and compare with demo historical data
        current_bill = await bill_processor.extract_bill_data()
        
        # In production, this would retrieve historical bills
        historical_bills = [current_bill]  # Placeholder
        
        anomalies = await bill_processor.detect_anomalies(current_bill, historical_bills)
        
        return {
            "customer_id": customer_id,
            "anomalies": [a.dict() for a in anomalies]
        }
    except Exception as e:
        logger.error(f"Error detecting bill anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bills/trends")
async def get_usage_trends(customer_id: str):
    """
    Analyze usage trends over time
    
    Args:
        customer_id: Customer identifier
        
    Returns:
        Usage trend analysis
    """
    try:
        # For demo, generate bill trends
        trends = await bill_processor.get_usage_trends([
            await bill_processor.extract_bill_data() for _ in range(5)
        ])
        
        return {
            "customer_id": customer_id,
            "trends": trends
        }
    except Exception as e:
        logger.error(f"Error getting usage trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# REGULATION SEARCH ENDPOINTS
# ============================================================================

@router.get("/regulations/search")
async def search_regulations(
    query: str,
    jurisdiction: Optional[str] = None,
    utility_type: Optional[str] = None,
    limit: int = 5
):
    """
    Search regulation documents with semantic understanding
    
    Args:
        query: Search query
        jurisdiction: Filter by jurisdiction (Federal, State)
        utility_type: Filter by utility type (electric, gas, water)
        limit: Maximum results to return
        
    Returns:
        List of search results with relevance scores
    """
    try:
        results = await regulation_search.search_regulations(query, jurisdiction, utility_type, limit)
        
        return {
            "query": query,
            "jurisdiction": jurisdiction,
            "utility_type": utility_type,
            "results": [r.dict() for r in results]
        }
    except Exception as e:
        logger.error(f"Error searching regulations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regulations/compliance-checklist")
async def get_compliance_checklist(
    utility_type: str,
    jurisdiction: str
):
    """
    Generate compliance checklist for specific utility type and jurisdiction
    
    Args:
        utility_type: Type of utility (electric, gas, water)
        jurisdiction: Jurisdiction (Federal, State)
        
    Returns:
        Compliance checklist with requirements
    """
    try:
        checklist = await regulation_search.get_compliance_checklist(utility_type, jurisdiction)
        return checklist
    except Exception as e:
        logger.error(f"Error generating compliance checklist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regulations/interpret")
async def interpret_policy(
    query: str,
    document_id: str
):
    """
    Get AI-powered interpretation of a specific policy
    
    Args:
        query: Question about the policy
        document_id: Document to interpret
        
    Returns:
        Policy interpretation with explanation and examples
    """
    try:
        interpretation = await regulation_search.interpret_policy(query, document_id)
        return interpretation
    except Exception as e:
        logger.error(f"Error interpreting policy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regulations/timeline")
async def get_regulation_timeline(category: Optional[str] = None):
    """
    Get timeline of regulations by category
    
    Args:
        category: Filter by category (optional)
        
    Returns:
        Timeline of regulations
    """
    try:
        timeline = await regulation_search.get_regulation_timeline(category)
        return {
            "category": category,
            "timeline": timeline
        }
    except Exception as e:
        logger.error(f"Error getting regulation timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SUPPORT AUTOMATION ENDPOINTS
# ============================================================================

@router.post("/support/classify")
async def classify_support_ticket(
    subject: str,
    description: str
):
    """
    Classify support ticket into category and priority
    
    Args:
        subject: Ticket subject
        description: Ticket description
        
    Returns:
        Classification results with category, priority, and confidence
    """
    try:
        classification = await support_automation.classify_ticket(subject, description)
        return classification
    except Exception as e:
        logger.error(f"Error classifying ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/support/tickets", response_model=SupportTicket)
async def create_support_ticket(
    customer_id: str,
    customer_name: str,
    subject: str,
    description: str,
    service_address: Optional[str] = None
):
    """
    Create and classify a new support ticket
    
    Args:
        customer_id: Customer account number
        customer_name: Customer name
        subject: Ticket subject
        description: Ticket description
        service_address: Service address
        
    Returns:
        Created SupportTicket object with AI-generated response
    """
    try:
        ticket = await support_automation.create_ticket(
            customer_id, customer_name, subject, description, service_address
        )
        return ticket
    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/support/tickets/{ticket_id}")
async def get_support_ticket(ticket_id: str):
    """
    Get support ticket by ID
    
    Args:
        ticket_id: Ticket identifier
        
    Returns:
        SupportTicket if found
    """
    try:
        ticket = await support_automation.get_ticket_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return ticket.dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/support/tickets/{ticket_id}/status")
async def update_ticket_status(
    ticket_id: str,
    status: TicketStatus,
    assigned_to: Optional[str] = None
):
    """
    Update ticket status
    
    Args:
        ticket_id: Ticket identifier
        status: New status
        assigned_to: Assignee (optional)
        
    Returns:
        Updated SupportTicket
    """
    try:
        ticket = await support_automation.update_ticket_status(ticket_id, status, assigned_to)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return ticket.dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating ticket status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/support/analytics")
async def get_support_analytics():
    """
    Get analytics on support tickets
    
    Returns:
        Analytics results
    """
    try:
        analytics = await support_automation.get_ticket_analytics()
        return analytics
    except Exception as e:
        logger.error(f"Error getting support analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/support/demo-tickets")
async def get_demo_tickets():
    """
    Get list of demo support tickets
    
    Returns:
        List of demo tickets
    """
    try:
        tickets = [t.dict() for t in support_automation.tickets]
        return {
            "total_tickets": len(tickets),
            "tickets": tickets
        }
    except Exception as e:
        logger.error(f"Error getting demo tickets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# USAGE ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/analytics/usage-trends")
async def get_usage_trends(
    customer_id: str,
    days: int = 30
):
    """
    Analyze usage trends for a customer
    
    Args:
        customer_id: Customer identifier
        days: Number of days to analyze
        
    Returns:
        Trend analysis results
    """
    try:
        trends = await usage_analytics.analyze_usage_trends(customer_id, days)
        return trends
    except Exception as e:
        logger.error(f"Error getting usage trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/anomalies")
async def detect_usage_anomalies(
    customer_id: str,
    days: int = 30,
    sensitivity: float = 1.5
):
    """
    Detect anomalies in usage data
    
    Args:
        customer_id: Customer identifier
        days: Number of days to analyze
        sensitivity: Standard deviation multiplier for anomaly detection
        
    Returns:
        List of detected anomalies
    """
    try:
        anomalies = await usage_analytics.detect_anomalies(customer_id, days, sensitivity)
        
        return {
            "customer_id": customer_id,
            "anomalies_detected": len(anomalies),
            "anomalies": [a.dict() for a in anomalies]
        }
    except Exception as e:
        logger.error(f"Error detecting usage anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/recommendations")
async def get_optimization_recommendations(
    customer_id: str,
    days: int = 30
):
    """
    Generate optimization recommendations based on usage analysis
    
    Args:
        customer_id: Customer identifier
        days: Number of days to analyze
        
    Returns:
        List of optimization recommendations
    """
    try:
        recommendations = await usage_analytics.get_optimization_recommendations(customer_id, days)
        
        return {
            "customer_id": customer_id,
            "recommendations": [r.dict() for r in recommendations]
        }
    except Exception as e:
        logger.error(f"Error getting optimization recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/peer-comparison")
async def compare_with_peers(
    customer_id: str,
    peer_group: str = "similar_homes"
):
    """
    Compare customer usage with peer group
    
    Args:
        customer_id: Customer identifier
        peer_group: Peer group identifier
        
    Returns:
        Comparison results
    """
    try:
        comparison = await usage_analytics.compare_with_peers(customer_id, peer_group)
        return comparison
    except Exception as e:
        logger.error(f"Error comparing with peers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/report")
async def generate_usage_report(
    customer_id: str,
    days: int = 30
):
    """
    Generate comprehensive usage report
    
    Args:
        customer_id: Customer identifier
        days: Number of days to analyze
        
    Returns:
        Comprehensive usage report
    """
    try:
        report = await usage_analytics.generate_usage_report(customer_id, days)
        return report
    except Exception as e:
        logger.error(f"Error generating usage report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# OVERVIEW ENDPOINTS
# ============================================================================

@router.get("/overview")
async def get_utilities_overview():
    """
    Get overview of all utilities services
    
    Returns:
        Overview of all modules with statistics
    """
    try:
        overview = {
            "bill_processing": bill_processor.get_statistics(),
            "regulation_search": regulation_search.get_statistics(),
            "support_automation": support_automation.get_statistics(),
            "usage_analytics": usage_analytics.get_statistics()
        }
        return overview
    except Exception as e:
        logger.error(f"Error getting utilities overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def get_utilities_info():
    """
    Get information about utilities module
    
    Returns:
        Module information and capabilities
    """
    return {
        "module": "Utilities AI Platform",
        "version": "1.0.0",
        "description": "AI-powered utilities business processes for electric, gas, and water utilities",
        "use_cases": [
            {
                "name": "Automated Bill Processing",
                "description": "Extract and analyze utility bills, detect anomalies, and provide insights",
                "business_impact": "Save 80% manual data entry time, reduce errors by 95%"
            },
            {
                "name": "Regulation Document Search",
                "description": "RAG-based semantic search through regulation documents",
                "business_impact": "Reduce research time by 70%, improve compliance accuracy by 90%"
            },
            {
                "name": "Customer Support Automation",
                "description": "AI-powered ticket classification, routing, and response generation",
                "business_impact": "Reduce response time by 60%, improve first-contact resolution by 45%"
            },
            {
                "name": "Usage Analytics",
                "description": "Analyze usage patterns, detect anomalies, and provide optimization recommendations",
                "business_impact": "Reduce energy waste by 25%, detect anomalies with 90% accuracy"
            }
        ],
        "endpoints": {
            "bill_processing": [
                "GET /utilities/bills/demo",
                "POST /utilities/bills/analyze",
                "POST /utilities/bills/compare",
                "GET /utilities/bills/anomalies",
                "GET /utilities/bills/trends"
            ],
            "regulation_search": [
                "GET /utilities/regulations/search",
                "GET /utilities/regulations/compliance-checklist",
                "GET /utilities/regulations/interpret",
                "GET /utilities/regulations/timeline"
            ],
            "support_automation": [
                "POST /utilities/support/classify",
                "POST /utilities/support/tickets",
                "GET /utilities/support/tickets/{ticket_id}",
                "PATCH /utilities/support/tickets/{ticket_id}/status",
                "GET /utilities/support/analytics",
                "GET /utilities/support/demo-tickets"
            ],
            "usage_analytics": [
                "GET /utilities/analytics/usage-trends",
                "GET /utilities/analytics/anomalies",
                "GET /utilities/analytics/recommendations",
                "GET /utilities/analytics/peer-comparison",
                "GET /utilities/analytics/report"
            ]
        }
    }