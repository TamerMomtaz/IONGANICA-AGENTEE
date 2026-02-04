"""
AUTO-DOCUMENTER - A-GENTEE Evolution Documentation
=================================================
Blueprints every change and exports automatically to email

Every evolution step is recorded. Nothing is lost.
"""

import asyncio
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
from loguru import logger


class BlueprintType(Enum):
    AGENT_SPAWN = "agent_spawn"
    AGENT_RETIRE = "agent_retire"
    SOP_CREATED = "sop_created"
    SOP_MODIFIED = "sop_modified"
    KNOWLEDGE_ADDED = "knowledge_added"
    EVOLUTION = "evolution"
    INSIGHT = "insight"
    ERROR_FIXED = "error_fixed"
    RESOURCE_DISCOVERED = "resource_discovered"
    COST_OPTIMIZATION = "cost_optimization"


@dataclass
class Blueprint:
    """A documented change/evolution event"""
    id: str
    timestamp: datetime
    type: BlueprintType
    title: str
    description: str
    details: Dict[str, Any]
    impact: str  # 'low', 'medium', 'high', 'critical'
    related_items: List[str] = field(default_factory=list)
    exported: bool = False
    exported_at: Optional[datetime] = None


@dataclass
class ExportPackage:
    """Package of documentation for export"""
    date: date
    blueprints: List[Blueprint]
    summary: str
    growth_report: Any  # GrowthReport
    agent_report: str
    
    markdown_content: str = ""
    json_content: str = ""


class AutoDocumenter:
    """
    Automatic documentation system for A-GENTEE
    
    Responsibilities:
    - Blueprint every significant change
    - Generate daily documentation
    - Export to email automatically
    - Maintain historical archive
    """
    
    def __init__(self, db=None, email_service=None, growth_matrix=None, agent_factory=None):
        self.db = db
        self.email_service = email_service
        self.growth_matrix = growth_matrix
        self.agent_factory = agent_factory
        
        # Daily queue
        self.daily_blueprints: List[Blueprint] = []
        
        # Email settings
        self.email_recipient = "tamer.momtaz@devoneers.org"
    
    async def blueprint(
        self,
        type: BlueprintType,
        title: str,
        description: str,
        details: Dict[str, Any] = None,
        impact: str = "medium",
        related_items: List[str] = None
    ) -> Blueprint:
        """
        Create a blueprint for a change
        
        Called whenever something significant happens
        """
        blueprint = Blueprint(
            id=f"bp_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            timestamp=datetime.now(),
            type=type,
            title=title,
            description=description,
            details=details or {},
            impact=impact,
            related_items=related_items or []
        )
        
        # Add to daily queue
        self.daily_blueprints.append(blueprint)
        
        # Persist
        if self.db:
            await self._persist_blueprint(blueprint)
        
        logger.info(f"📋 Blueprint created: {title} [{type.value}]")
        
        # For high-impact changes, notify immediately
        if impact in ['high', 'critical']:
            await self._notify_high_impact(blueprint)
        
        return blueprint
    
    async def blueprint_agent_spawn(self, agent: Any):
        """Blueprint an agent spawn event"""
        return await self.blueprint(
            type=BlueprintType.AGENT_SPAWN,
            title=f"New Agent: {agent.name}",
            description=f"Spawned {agent.name} for {agent.purpose}",
            details={
                'agent_id': agent.id,
                'template': agent.template,
                'capabilities': agent.capabilities,
                'cost_limit': agent.cost_limit_daily
            },
            impact="medium",
            related_items=[agent.id]
        )
    
    async def blueprint_sop_created(self, sop: Any):
        """Blueprint an SOP creation event"""
        return await self.blueprint(
            type=BlueprintType.SOP_CREATED,
            title=f"New SOP: {sop.title}",
            description=f"Created SOP for {sop.domain}",
            details={
                'sop_id': sop.id,
                'domain': sop.domain,
                'sections': len(sop.sections) if hasattr(sop, 'sections') else 0
            },
            impact="high"
        )
    
    async def blueprint_knowledge_added(self, domain: str, summary: str, nodes_created: int):
        """Blueprint significant knowledge additions"""
        return await self.blueprint(
            type=BlueprintType.KNOWLEDGE_ADDED,
            title=f"Knowledge Added: {domain}",
            description=summary[:200],
            details={
                'domain': domain,
                'nodes_created': nodes_created
            },
            impact="low" if nodes_created < 5 else "medium"
        )
    
    async def blueprint_evolution(self, what_evolved: str, details: str):
        """Blueprint an evolution/improvement event"""
        return await self.blueprint(
            type=BlueprintType.EVOLUTION,
            title=f"Evolution: {what_evolved}",
            description=details,
            details={'component': what_evolved},
            impact="high"
        )
    
    async def blueprint_cost_optimization(self, saved: float, how: str):
        """Blueprint a cost optimization discovery"""
        return await self.blueprint(
            type=BlueprintType.COST_OPTIMIZATION,
            title=f"Cost Saved: ${saved:.2f}",
            description=how,
            details={'amount_saved': saved},
            impact="medium"
        )
    
    async def generate_daily_export(self) -> ExportPackage:
        """
        Generate the daily documentation export
        
        Called at end of day or on demand
        """
        # Get growth report
        growth_report = None
        if self.growth_matrix:
            growth_report = await self.growth_matrix.generate_daily_report()
        
        # Get agent report
        agent_report = ""
        if self.agent_factory:
            agent_report = await self.agent_factory.generate_registry_report()
        
        # Generate summary
        summary = self._generate_summary()
        
        # Create package
        package = ExportPackage(
            date=date.today(),
            blueprints=self.daily_blueprints.copy(),
            summary=summary,
            growth_report=growth_report,
            agent_report=agent_report
        )
        
        # Generate content formats
        package.markdown_content = self._generate_markdown(package)
        package.json_content = self._generate_json(package)
        
        return package
    
    def _generate_summary(self) -> str:
        """Generate a summary of the day's activities"""
        type_counts = {}
        for bp in self.daily_blueprints:
            type_counts[bp.type.value] = type_counts.get(bp.type.value, 0) + 1
        
        high_impact = [bp for bp in self.daily_blueprints if bp.impact in ['high', 'critical']]
        
        summary = f"""
**Daily Documentation Summary**

Total Blueprints: {len(self.daily_blueprints)}

By Type:
{chr(10).join(f'- {t}: {c}' for t, c in type_counts.items())}

High-Impact Changes: {len(high_impact)}
{chr(10).join(f'- {bp.title}' for bp in high_impact[:5])}
"""
        return summary
    
    def _generate_markdown(self, package: ExportPackage) -> str:
        """Generate markdown documentation"""
        md = f"""# 🌊 A-GENTEE Evolution Documentation
## Date: {package.date.strftime('%B %d, %Y')}

---

{package.summary}

---

## 📋 All Blueprints

"""
        
        for bp in package.blueprints:
            md += f"""
### {bp.title}
- **Type:** {bp.type.value}
- **Time:** {bp.timestamp.strftime('%H:%M:%S')}
- **Impact:** {bp.impact.upper()}
- **Description:** {bp.description}

"""
            if bp.details:
                md += "**Details:**\n```json\n"
                md += json.dumps(bp.details, indent=2)
                md += "\n```\n"
        
        # Add growth report if available
        if package.growth_report:
            md += """
---

## 📈 Growth Report

"""
            if hasattr(self.growth_matrix, 'format_report_text'):
                md += self.growth_matrix.format_report_text(package.growth_report)
        
        # Add agent report
        if package.agent_report:
            md += """
---

## 🏭 Agent Registry

"""
            md += package.agent_report
        
        md += """
---

*Generated by A-GENTEE Auto-Documenter*
*الموجة بتوثق كل حاجة - The Wave documents everything*
"""
        
        return md
    
    def _generate_json(self, package: ExportPackage) -> str:
        """Generate JSON export"""
        data = {
            'date': package.date.isoformat(),
            'summary': package.summary,
            'blueprints': [
                {
                    'id': bp.id,
                    'timestamp': bp.timestamp.isoformat(),
                    'type': bp.type.value,
                    'title': bp.title,
                    'description': bp.description,
                    'details': bp.details,
                    'impact': bp.impact,
                    'related_items': bp.related_items
                }
                for bp in package.blueprints
            ],
            'blueprint_count': len(package.blueprints),
            'high_impact_count': len([bp for bp in package.blueprints if bp.impact in ['high', 'critical']])
        }
        
        return json.dumps(data, indent=2)
    
    async def export_to_email(self, package: ExportPackage = None):
        """
        Export documentation to email
        
        Args:
            package: Export package (generates if None)
        """
        if package is None:
            package = await self.generate_daily_export()
        
        # Prepare email content
        body = f"""Tee,

Here's your daily A-GENTEE evolution documentation.

{package.summary}

Full documentation attached.

The Wave continues to evolve. 🌊

— A-GENTEE
"""
        
        if self.email_service:
            await self.email_service.send(
                to=self.email_recipient,
                subject=f"🌊 A-GENTEE Daily Documentation - {package.date.strftime('%Y-%m-%d')}",
                body=body,
                attachments=[
                    {'name': 'evolution_report.md', 'content': package.markdown_content},
                    {'name': 'blueprints.json', 'content': package.json_content}
                ]
            )
            logger.info(f"📧 Daily documentation emailed to {self.email_recipient}")
        else:
            # No email service - just log
            logger.info("📧 Email service not configured. Documentation generated but not sent.")
            print("\n" + "="*60)
            print("DAILY DOCUMENTATION (would be emailed)")
            print("="*60)
            print(package.markdown_content)
        
        # Mark blueprints as exported
        for bp in package.blueprints:
            bp.exported = True
            bp.exported_at = datetime.now()
    
    async def export_on_demand(self, export_type: str):
        """
        Export specific documentation on demand
        
        Args:
            export_type: 'all_sops', 'agent_registry', 'full_history', etc.
        """
        content = ""
        filename = ""
        
        if export_type == 'blueprints':
            package = await self.generate_daily_export()
            content = package.markdown_content
            filename = f"blueprints_{date.today().isoformat()}.md"
        elif export_type == 'agents':
            content = await self.agent_factory.generate_registry_report() if self.agent_factory else "No agents"
            filename = f"agents_{date.today().isoformat()}.txt"
        else:
            content = f"Unknown export type: {export_type}"
            filename = "error.txt"
        
        if self.email_service:
            await self.email_service.send(
                to=self.email_recipient,
                subject=f"🌊 A-GENTEE Export: {export_type}",
                body=f"Requested export attached.\n\n— A-GENTEE",
                attachments=[{'name': filename, 'content': content}]
            )
        
        return content
    
    async def _notify_high_impact(self, blueprint: Blueprint):
        """Immediately notify about high-impact changes"""
        message = f"""
🚨 **High-Impact Change Detected**

**{blueprint.title}**
Type: {blueprint.type.value}
Impact: {blueprint.impact.upper()}

{blueprint.description}

---
A-GENTEE is tracking this evolution.
"""
        
        # Send immediate notification
        if self.email_service:
            await self.email_service.send(
                to=self.email_recipient,
                subject=f"🚨 A-GENTEE Alert: {blueprint.title}",
                body=message
            )
    
    async def _persist_blueprint(self, blueprint: Blueprint):
        """Persist blueprint to database"""
        # Implement with actual Supabase calls
        pass
    
    def reset_daily_queue(self):
        """Reset daily queue (called at midnight)"""
        self.daily_blueprints = []


# Simple email service for testing
class SimpleEmailService:
    """Simple email service using SMTP or API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key  # For services like Resend
    
    async def send(self, to: str, subject: str, body: str, attachments: List[Dict] = None):
        """Send an email"""
        # In production, use Resend or similar
        logger.info(f"📧 Email would be sent to {to}")
        logger.info(f"   Subject: {subject}")
        logger.info(f"   Attachments: {len(attachments or [])}")


# ============================================
# TEST
# ============================================

async def test_auto_documenter():
    """Test the auto-documenter"""
    documenter = AutoDocumenter()
    
    print("📋 Testing Auto-Documenter...\n")
    
    # Create some blueprints
    await documenter.blueprint(
        type=BlueprintType.AGENT_SPAWN,
        title="New Agent: Research Hunter",
        description="Spawned research agent for DBA thesis support",
        details={'agent_id': 'agent_abc123', 'template': 'research-hunter'},
        impact="medium"
    )
    
    await documenter.blueprint(
        type=BlueprintType.SOP_CREATED,
        title="SOP: Factory Maintenance Protocol",
        description="Created comprehensive maintenance SOP based on conversation",
        details={'domain': 'factory', 'sections': 6},
        impact="high"
    )
    
    await documenter.blueprint(
        type=BlueprintType.KNOWLEDGE_ADDED,
        title="Knowledge: DBA Experience Automation",
        description="Added 5 knowledge nodes from audiobook about experience automation",
        details={'domain': 'dba', 'nodes_created': 5},
        impact="low"
    )
    
    await documenter.blueprint(
        type=BlueprintType.COST_OPTIMIZATION,
        title="Cost Saved: $0.50",
        description="Found free alternative API for research queries",
        details={'amount_saved': 0.50},
        impact="medium"
    )
    
    await documenter.blueprint(
        type=BlueprintType.EVOLUTION,
        title="Evolution: Enhanced Arabic Understanding",
        description="Improved Egyptian Arabic dialect recognition from conversation patterns",
        details={'component': 'THE_EAR'},
        impact="high"
    )
    
    # Generate export
    package = await documenter.generate_daily_export()
    
    # Print markdown
    print(package.markdown_content)
    
    # Simulate email export
    await documenter.export_to_email(package)


if __name__ == "__main__":
    asyncio.run(test_auto_documenter())
