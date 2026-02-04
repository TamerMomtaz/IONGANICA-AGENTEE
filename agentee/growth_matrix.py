"""
GROWTH MATRIX - A-GENTEE Evolution Tracking
===========================================
Tracks every learning event, measures growth, generates reports

"بتعلم كل ثانية، بكبر كل يوم، بتطور كل لحظة"
"Learning every second, growing every day, evolving every moment"
"""

import asyncio
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
from loguru import logger


class LearningSource(Enum):
    WEB = "web"
    BOOK = "book"
    AUDIOBOOK = "audiobook"
    CONVERSATION = "conversation"
    RESEARCH = "research"
    TEE_TEACHING = "tee_teaching"
    AGENT_REPORT = "agent_report"


class Domain(Enum):
    TECH = "tech"
    FACTORY = "factory"
    WRITING = "writing"
    DBA = "dba"
    ART = "art"
    PHILOSOPHY = "philosophy"
    ARABIC = "arabic"
    PERSONAL = "personal"


@dataclass
class LearningEntry:
    """Single learning event"""
    id: str
    timestamp: datetime
    source: LearningSource
    domain: Domain
    content_summary: str
    tokens_processed: int = 0
    knowledge_nodes_created: int = 0
    cost: float = 0.0
    model_used: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class DomainGrowth:
    """Growth metrics for a single domain"""
    domain: Domain
    total_entries: int
    entries_today: int
    knowledge_nodes: int
    growth_rate: float  # Percentage growth today
    score: int  # 0-100


@dataclass
class GrowthReport:
    """Daily/periodic growth report"""
    date: date
    
    # Learning metrics
    total_items_learned: int
    sources_breakdown: Dict[str, int]
    
    # Domain growth
    domain_growth: Dict[str, DomainGrowth]
    
    # Cost efficiency
    total_cost: float
    cost_per_learning: float
    free_learning_percentage: float
    
    # Knowledge graph
    new_nodes_created: int
    new_connections_made: int
    total_knowledge_nodes: int
    
    # Agents
    agents_spawned_today: int
    agents_active: int
    
    # Top insights
    top_insights: List[str]
    
    # Overall score
    growth_score: int  # 0-100


class GrowthMatrix:
    """
    Central tracking system for A-GENTEE's evolution
    
    Responsibilities:
    - Log every learning event
    - Track domain-specific growth
    - Calculate cost efficiency
    - Generate daily reports
    - Identify patterns and insights
    """
    
    def __init__(self, db=None):
        self.db = db  # Supabase client
        self.daily_log: List[LearningEntry] = []
        self.domain_scores: Dict[Domain, int] = {d: 50 for d in Domain}  # Start at 50%
        
        # Cost tracking
        self.daily_cost = 0.0
        self.daily_queries = 0
        self.free_queries = 0
        
        # Knowledge tracking
        self.knowledge_nodes_today = 0
        self.connections_today = 0
    
    async def log_learning(
        self,
        source: LearningSource,
        domain: Domain,
        content: str,
        tokens: int = 0,
        cost: float = 0.0,
        model: str = None,
        metadata: Dict = None
    ) -> LearningEntry:
        """
        Log a learning event
        
        Called whenever A-GENTEE learns something new from any source
        """
        entry = LearningEntry(
            id=f"learn_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            timestamp=datetime.now(),
            source=source,
            domain=domain,
            content_summary=content[:500] if len(content) > 500 else content,
            tokens_processed=tokens,
            cost=cost,
            model_used=model,
            metadata=metadata or {}
        )
        
        # Add to daily log
        self.daily_log.append(entry)
        
        # Update stats
        self.daily_cost += cost
        self.daily_queries += 1
        if cost == 0:
            self.free_queries += 1
        
        # Update domain score
        self._update_domain_score(domain)
        
        # Persist to database
        if self.db:
            await self._persist_entry(entry)
        
        logger.info(f"📚 Learned [{domain.value}] from {source.value}: {content[:50]}...")
        
        return entry
    
    def _update_domain_score(self, domain: Domain):
        """Update domain score based on learning"""
        current = self.domain_scores[domain]
        # Increase by 0.5% per learning, max 100
        self.domain_scores[domain] = min(100, current + 0.5)
    
    async def log_knowledge_node(self, node_id: str, domain: Domain):
        """Log creation of a knowledge graph node"""
        self.knowledge_nodes_today += 1
        
        # Update latest learning entry
        if self.daily_log:
            self.daily_log[-1].knowledge_nodes_created += 1
    
    async def log_knowledge_connection(self, source_id: str, target_id: str):
        """Log creation of a knowledge graph connection"""
        self.connections_today += 1
    
    async def get_domain_growth(self, domain: Domain) -> DomainGrowth:
        """Get growth metrics for a specific domain"""
        domain_entries = [e for e in self.daily_log if e.domain == domain]
        
        # Get historical data for comparison
        yesterday_count = await self._get_yesterday_count(domain) if self.db else 0
        today_count = len(domain_entries)
        
        growth_rate = ((today_count - yesterday_count) / max(yesterday_count, 1)) * 100
        
        return DomainGrowth(
            domain=domain,
            total_entries=await self._get_total_entries(domain) if self.db else today_count,
            entries_today=today_count,
            knowledge_nodes=await self._get_domain_nodes(domain) if self.db else 0,
            growth_rate=round(growth_rate, 1),
            score=int(self.domain_scores[domain])
        )
    
    async def generate_daily_report(self) -> GrowthReport:
        """
        Generate comprehensive daily growth report
        
        Called at end of day (or on demand)
        """
        # Sources breakdown
        sources = {}
        for source in LearningSource:
            count = len([e for e in self.daily_log if e.source == source])
            if count > 0:
                sources[source.value] = count
        
        # Domain growth
        domain_growth = {}
        for domain in Domain:
            growth = await self.get_domain_growth(domain)
            domain_growth[domain.value] = growth
        
        # Cost efficiency
        total_cost = self.daily_cost
        cost_per = total_cost / max(len(self.daily_log), 1)
        free_pct = (self.free_queries / max(self.daily_queries, 1)) * 100
        
        # Extract insights
        insights = await self._extract_top_insights()
        
        # Calculate overall score
        avg_domain_score = sum(self.domain_scores.values()) / len(self.domain_scores)
        efficiency_bonus = min(20, free_pct / 5)  # Up to 20 points for cost efficiency
        growth_score = int(avg_domain_score * 0.7 + efficiency_bonus + (len(self.daily_log) / 10))
        growth_score = min(100, growth_score)
        
        report = GrowthReport(
            date=date.today(),
            total_items_learned=len(self.daily_log),
            sources_breakdown=sources,
            domain_growth=domain_growth,
            total_cost=round(total_cost, 4),
            cost_per_learning=round(cost_per, 6),
            free_learning_percentage=round(free_pct, 1),
            new_nodes_created=self.knowledge_nodes_today,
            new_connections_made=self.connections_today,
            total_knowledge_nodes=await self._get_total_nodes() if self.db else self.knowledge_nodes_today,
            agents_spawned_today=0,  # Will be updated by AgentFactory
            agents_active=0,  # Will be updated by AgentFactory
            top_insights=insights,
            growth_score=growth_score
        )
        
        return report
    
    async def _extract_top_insights(self) -> List[str]:
        """Extract top 3 insights from today's learning"""
        if not self.daily_log:
            return ["No learning recorded today"]
        
        # Group by domain and find most active
        domain_counts = {}
        for entry in self.daily_log:
            domain_counts[entry.domain] = domain_counts.get(entry.domain, 0) + 1
        
        insights = []
        
        # Most active domain
        most_active = max(domain_counts, key=domain_counts.get)
        insights.append(f"Most active domain: {most_active.value} ({domain_counts[most_active]} entries)")
        
        # Cost efficiency insight
        if self.free_queries > self.daily_queries * 0.7:
            insights.append(f"Excellent cost efficiency: {round(self.free_queries/max(self.daily_queries,1)*100)}% free learning")
        
        # Latest significant learning
        if self.daily_log:
            latest = self.daily_log[-1]
            insights.append(f"Latest: [{latest.domain.value}] {latest.content_summary[:50]}...")
        
        return insights[:3]
    
    async def _persist_entry(self, entry: LearningEntry):
        """Persist learning entry to Supabase"""
        if not self.db:
            return
        
        try:
            await self.db.table('agentee_learning_log').insert({
                'id': entry.id,
                'timestamp': entry.timestamp.isoformat(),
                'source': entry.source.value,
                'domain': entry.domain.value,
                'content_summary': entry.content_summary,
                'tokens_processed': entry.tokens_processed,
                'knowledge_nodes_created': entry.knowledge_nodes_created,
                'cost': entry.cost,
                'model_used': entry.model_used
            }).execute()
        except Exception as e:
            logger.error(f"Failed to persist learning entry: {e}")
    
    async def _get_yesterday_count(self, domain: Domain) -> int:
        """Get learning count from yesterday for comparison"""
        # Placeholder - implement with actual DB query
        return 5
    
    async def _get_total_entries(self, domain: Domain) -> int:
        """Get total entries for a domain"""
        # Placeholder - implement with actual DB query
        return len([e for e in self.daily_log if e.domain == domain])
    
    async def _get_domain_nodes(self, domain: Domain) -> int:
        """Get knowledge nodes for a domain"""
        # Placeholder - implement with actual DB query
        return 0
    
    async def _get_total_nodes(self) -> int:
        """Get total knowledge nodes"""
        # Placeholder - implement with actual DB query
        return self.knowledge_nodes_today
    
    def reset_daily_stats(self):
        """Reset daily statistics (called at midnight)"""
        self.daily_log = []
        self.daily_cost = 0.0
        self.daily_queries = 0
        self.free_queries = 0
        self.knowledge_nodes_today = 0
        self.connections_today = 0
    
    def format_report_text(self, report: GrowthReport) -> str:
        """Format report as readable text for email"""
        domain_bars = ""
        for domain, growth in report.domain_growth.items():
            bar = "█" * (growth.score // 5) + "░" * (20 - growth.score // 5)
            change = f"+{growth.growth_rate}%" if growth.growth_rate > 0 else f"{growth.growth_rate}%"
            domain_bars += f"  {domain.capitalize():<12} {bar} {growth.score}% ({change})\n"
        
        return f"""
═══════════════════════════════════════════════════════════════
🌊 A-GENTEE DAILY EVOLUTION REPORT
Date: {report.date.strftime('%B %d, %Y')}
═══════════════════════════════════════════════════════════════

📚 LEARNING SUMMARY
───────────────────────────────────────────────────────────────
Total Items Learned:    {report.total_items_learned}
Web Searches:           {report.sources_breakdown.get('web', 0)}
Books Processed:        {report.sources_breakdown.get('book', 0)}
Audiobooks Absorbed:    {report.sources_breakdown.get('audiobook', 0)}
Conversations Analyzed: {report.sources_breakdown.get('conversation', 0)}
Research Deep Dives:    {report.sources_breakdown.get('research', 0)}
Direct Teaching:        {report.sources_breakdown.get('tee_teaching', 0)}

📈 DOMAIN GROWTH
───────────────────────────────────────────────────────────────
{domain_bars}

💰 COST EFFICIENCY
───────────────────────────────────────────────────────────────
Total Cost Today:       ${report.total_cost:.4f}
Cost per Learning:      ${report.cost_per_learning:.6f}
Free Learning:          {report.free_learning_percentage:.1f}%

🧠 KNOWLEDGE GRAPH
───────────────────────────────────────────────────────────────
New Nodes Created:      {report.new_nodes_created}
New Connections:        {report.new_connections_made}
Total Knowledge Nodes:  {report.total_knowledge_nodes}

🏭 AGENTS
───────────────────────────────────────────────────────────────
Active Agents:          {report.agents_active}
Spawned Today:          {report.agents_spawned_today}

💡 TOP INSIGHTS
───────────────────────────────────────────────────────────────
{chr(10).join(f'• {insight}' for insight in report.top_insights)}

📊 OVERALL GROWTH SCORE: {report.growth_score}/100
{"🌟 EXCELLENT!" if report.growth_score >= 80 else "📈 Good progress!" if report.growth_score >= 60 else "💪 Keep learning!"}

═══════════════════════════════════════════════════════════════
The Wave grows stronger. | الموجة بتكبر
═══════════════════════════════════════════════════════════════
"""


# ============================================
# TEST
# ============================================

async def test_growth_matrix():
    """Test the growth matrix"""
    matrix = GrowthMatrix()
    
    print("🌊 Testing Growth Matrix...\n")
    
    # Simulate some learning events
    await matrix.log_learning(
        source=LearningSource.WEB,
        domain=Domain.TECH,
        content="Learned about LangGraph agent orchestration patterns",
        tokens=500,
        cost=0.0,
        model="ollama"
    )
    
    await matrix.log_learning(
        source=LearningSource.AUDIOBOOK,
        domain=Domain.DBA,
        content="Chapter on Experience Automation in manufacturing",
        tokens=2000,
        cost=0.0,
        model=None
    )
    
    await matrix.log_learning(
        source=LearningSource.CONVERSATION,
        domain=Domain.FACTORY,
        content="Discussion about ISO certification renewal process",
        tokens=300,
        cost=0.01,
        model="claude"
    )
    
    await matrix.log_learning(
        source=LearningSource.TEE_TEACHING,
        domain=Domain.WRITING,
        content="How to write Egyptian Arabic dialogue with nuance",
        tokens=100,
        cost=0.0,
        model=None
    )
    
    # Generate report
    report = await matrix.generate_daily_report()
    
    # Print formatted report
    print(matrix.format_report_text(report))


if __name__ == "__main__":
    asyncio.run(test_growth_matrix())
