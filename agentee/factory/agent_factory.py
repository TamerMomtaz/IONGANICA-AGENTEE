"""
AGENT FACTORY - A-GENTEE Sub-Agent Management
=============================================
Spawns, trains, monitors, and retires specialized sub-agents

A-GENTEE is not alone. It creates children.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
from loguru import logger


class AgentStatus(Enum):
    INITIALIZING = "initializing"
    TRAINING = "training"
    ACTIVE = "active"
    PAUSED = "paused"
    RETIRED = "retired"


class AgentLifespan(Enum):
    TASK = "task_complete"      # Dies after completing task
    SESSION = "session"          # Dies when Tee ends session
    PERSISTENT = "persistent"    # Lives until explicitly retired
    TIMED = "timed"              # Lives for specified duration


@dataclass
class AgentTemplate:
    """Template for creating agents"""
    name: str
    purpose: str
    capabilities: List[str]
    lifespan: AgentLifespan
    cost_limit_daily: float
    default_model: str
    training_data: List[str] = field(default_factory=list)
    auto_spawn_triggers: List[str] = field(default_factory=list)


@dataclass
class SpawnedAgent:
    """A spawned sub-agent instance"""
    id: str
    template: str
    name: str
    purpose: str
    status: AgentStatus
    capabilities: List[str]
    lifespan: AgentLifespan
    cost_limit_daily: float
    cost_today: float
    model: str
    
    # Performance metrics
    tasks_completed: int = 0
    tasks_failed: int = 0
    success_rate: float = 100.0
    
    # Training
    training_data: List[str] = field(default_factory=list)
    training_score: int = 0  # 0-100
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    retired_at: Optional[datetime] = None
    
    # Parent
    parent: str = "agentee"


# Pre-defined templates
AGENT_TEMPLATES = {
    'sop-builder': AgentTemplate(
        name='SOP Builder',
        purpose='Create and modify Standard Operating Procedures',
        capabilities=['sop_creation', 'sop_modification', 'process_analysis', 'documentation'],
        lifespan=AgentLifespan.PERSISTENT,
        cost_limit_daily=0.20,
        default_model='claude',
        auto_spawn_triggers=['create an sop', 'make a procedure', 'document the process']
    ),
    
    'research-hunter': AgentTemplate(
        name='Research Hunter',
        purpose='Deep research on any topic',
        capabilities=['web_search', 'paper_analysis', 'summarization', 'citation'],
        lifespan=AgentLifespan.TASK,
        cost_limit_daily=0.30,
        default_model='gemini',
        auto_spawn_triggers=['research everything about', 'find all information on', 'deep dive into']
    ),
    
    'code-fixer': AgentTemplate(
        name='Code Fixer',
        purpose='Detect and fix code issues autonomously',
        capabilities=['code_analysis', 'bug_detection', 'auto_fix', 'testing'],
        lifespan=AgentLifespan.PERSISTENT,
        cost_limit_daily=0.25,
        default_model='claude',
        auto_spawn_triggers=['fix this code', 'debug', 'there is a bug']
    ),
    
    'quality-eye': AgentTemplate(
        name='Quality Eye',
        purpose='QA for specific products',
        capabilities=['quality_check', 'consistency_analysis', 'improvement_suggestions'],
        lifespan=AgentLifespan.PERSISTENT,
        cost_limit_daily=0.15,
        default_model='claude',
        auto_spawn_triggers=['check quality', 'review this', 'qa']
    ),
    
    'learning-scout': AgentTemplate(
        name='Learning Scout',
        purpose='Find new learning resources autonomously',
        capabilities=['resource_discovery', 'relevance_scoring', 'cost_analysis'],
        lifespan=AgentLifespan.PERSISTENT,
        cost_limit_daily=0.10,
        default_model='ollama',
        auto_spawn_triggers=[]  # Runs on schedule, not trigger
    ),
    
    'factory-advisor': AgentTemplate(
        name='Factory Advisor',
        purpose='Help with plant operations and industrial matters',
        capabilities=['operations_advice', 'iso_compliance', 'maintenance_planning', 'quality_control'],
        lifespan=AgentLifespan.PERSISTENT,
        cost_limit_daily=0.20,
        default_model='claude',
        training_data=['AMCF procedures', 'ISO standards', 'Petrochemical processes'],
        auto_spawn_triggers=['at the plant', 'factory', 'production', 'maintenance']
    ),
    
    'dba-tutor': AgentTemplate(
        name='DBA Tutor',
        purpose='Help with doctoral studies',
        capabilities=['academic_research', 'thesis_assistance', 'paper_review', 'methodology_advice'],
        lifespan=AgentLifespan.PERSISTENT,
        cost_limit_daily=0.30,
        default_model='gemini',
        auto_spawn_triggers=['dba', 'thesis', 'doctoral', 'research methodology']
    ),
    
    'book-companion': AgentTemplate(
        name='Book Companion',
        purpose='Help with creative writing',
        capabilities=['story_continuation', 'character_development', 'arabic_prose', 'dialogue_writing'],
        lifespan=AgentLifespan.SESSION,
        cost_limit_daily=0.40,
        default_model='claude',
        training_data=['مش كتاب style', 'Tee writing patterns', 'Egyptian Arabic nuances'],
        auto_spawn_triggers=['continue the story', 'write chapter', 'help with my book']
    ),
    
    'creative-muse': AgentTemplate(
        name='Creative Muse',
        purpose='Inspire and help with creative work',
        capabilities=['lyrics_continuation', 'poetry', 'idea_generation', 'artistic_analysis'],
        lifespan=AgentLifespan.SESSION,
        cost_limit_daily=0.35,
        default_model='claude',
        auto_spawn_triggers=['lyrics', 'poem', 'creative', 'inspiration']
    ),
    
    'audible-learner': AgentTemplate(
        name='Audible Learner',
        purpose='Learn from audiobooks passively',
        capabilities=['audio_processing', 'knowledge_extraction', 'insight_generation'],
        lifespan=AgentLifespan.PERSISTENT,
        cost_limit_daily=0.05,  # Very cheap - mostly uses Whisper
        default_model='ollama',
        auto_spawn_triggers=[]  # Always running when audio detected
    )
}


class AgentFactory:
    """
    Factory for creating and managing A-GENTEE's sub-agents
    
    Responsibilities:
    - Spawn agents from templates
    - Train agents with specific knowledge
    - Monitor agent performance
    - Retire underperforming or completed agents
    - Report on all agents to Tee
    """
    
    def __init__(self, db=None, notifier=None):
        self.db = db
        self.notifier = notifier
        self.agents: Dict[str, SpawnedAgent] = {}
        self.templates = AGENT_TEMPLATES
        
    async def spawn_agent(
        self,
        template_name: str,
        custom_name: Optional[str] = None,
        custom_purpose: Optional[str] = None,
        extra_training: List[str] = None
    ) -> SpawnedAgent:
        """
        Spawn a new agent from a template
        
        Args:
            template_name: Name of the template to use
            custom_name: Optional custom name for this instance
            custom_purpose: Optional custom purpose
            extra_training: Additional training data
            
        Returns:
            The spawned agent
        """
        if template_name not in self.templates:
            raise ValueError(f"Unknown template: {template_name}")
        
        template = self.templates[template_name]
        
        # Create agent
        agent = SpawnedAgent(
            id=f"agent_{uuid.uuid4().hex[:8]}",
            template=template_name,
            name=custom_name or template.name,
            purpose=custom_purpose or template.purpose,
            status=AgentStatus.INITIALIZING,
            capabilities=template.capabilities,
            lifespan=template.lifespan,
            cost_limit_daily=template.cost_limit_daily,
            cost_today=0.0,
            model=template.default_model,
            training_data=template.training_data + (extra_training or [])
        )
        
        logger.info(f"🏭 Spawning agent: {agent.name} ({agent.id})")
        
        # Train the agent
        await self._train_agent(agent)
        
        # Activate
        agent.status = AgentStatus.ACTIVE
        
        # Register
        self.agents[agent.id] = agent
        
        # Persist
        if self.db:
            await self._persist_agent(agent)
        
        # Notify Tee
        await self._notify_spawn(agent)
        
        return agent
    
    async def _train_agent(self, agent: SpawnedAgent):
        """Train an agent with its training data"""
        agent.status = AgentStatus.TRAINING
        
        if not agent.training_data:
            agent.training_score = 100
            return
        
        # Simulate training (in reality, this would involve
        # loading knowledge into the agent's context)
        logger.info(f"📚 Training {agent.name} with {len(agent.training_data)} items...")
        
        for i, item in enumerate(agent.training_data):
            # Each training item increases score
            agent.training_score = min(100, (i + 1) * (100 // len(agent.training_data)))
            await asyncio.sleep(0.1)  # Simulate training time
        
        agent.training_score = 100
        logger.info(f"✅ {agent.name} training complete. Score: {agent.training_score}/100")
    
    async def _notify_spawn(self, agent: SpawnedAgent):
        """Notify Tee about the new agent"""
        message = f"""
🏭 **New Agent Spawned!**

**Name:** {agent.name}
**ID:** {agent.id}
**Purpose:** {agent.purpose}
**Capabilities:** {', '.join(agent.capabilities)}
**Cost Limit:** ${agent.cost_limit_daily}/day
**Lifespan:** {agent.lifespan.value}
**Model:** {agent.model}
**Training Score:** {agent.training_score}/100

The agent is now **ACTIVE** and ready to help.
"""
        
        if self.notifier:
            await self.notifier.notify(message)
        else:
            print(message)
    
    async def get_agent(self, agent_id: str) -> Optional[SpawnedAgent]:
        """Get an agent by ID"""
        return self.agents.get(agent_id)
    
    async def get_active_agents(self) -> List[SpawnedAgent]:
        """Get all active agents"""
        return [a for a in self.agents.values() if a.status == AgentStatus.ACTIVE]
    
    async def retire_agent(self, agent_id: str, reason: str = "Completed"):
        """Retire an agent"""
        agent = self.agents.get(agent_id)
        if not agent:
            return
        
        agent.status = AgentStatus.RETIRED
        agent.retired_at = datetime.now()
        
        logger.info(f"👋 Retiring agent: {agent.name}. Reason: {reason}")
        
        if self.db:
            await self._update_agent(agent)
        
        # Notify
        if self.notifier:
            await self.notifier.notify(f"Agent {agent.name} retired. Reason: {reason}")
    
    async def record_task_completion(self, agent_id: str, success: bool, cost: float):
        """Record a task completion for an agent"""
        agent = self.agents.get(agent_id)
        if not agent:
            return
        
        if success:
            agent.tasks_completed += 1
        else:
            agent.tasks_failed += 1
        
        agent.cost_today += cost
        agent.last_active = datetime.now()
        
        # Update success rate
        total = agent.tasks_completed + agent.tasks_failed
        agent.success_rate = (agent.tasks_completed / total) * 100 if total > 0 else 100
        
        # Check cost limit
        if agent.cost_today >= agent.cost_limit_daily:
            logger.warning(f"⚠️ Agent {agent.name} reached daily cost limit!")
            agent.status = AgentStatus.PAUSED
            
            if self.notifier:
                await self.notifier.notify(
                    f"⚠️ Agent {agent.name} paused - reached ${agent.cost_limit_daily} daily limit"
                )
    
    async def generate_registry_report(self) -> str:
        """Generate a report of all agents"""
        active = [a for a in self.agents.values() if a.status == AgentStatus.ACTIVE]
        paused = [a for a in self.agents.values() if a.status == AgentStatus.PAUSED]
        retired = [a for a in self.agents.values() if a.status == AgentStatus.RETIRED]
        
        report = """
═══════════════════════════════════════════════════════════════
🏭 A-GENTEE AGENT REGISTRY
═══════════════════════════════════════════════════════════════

"""
        
        if active:
            report += "🟢 ACTIVE AGENTS\n"
            report += "───────────────────────────────────────────────────────────────\n"
            for agent in active:
                report += f"""
  {agent.name} ({agent.id})
  ├── Purpose: {agent.purpose[:50]}...
  ├── Tasks: {agent.tasks_completed} completed, {agent.tasks_failed} failed
  ├── Success Rate: {agent.success_rate:.1f}%
  ├── Cost Today: ${agent.cost_today:.4f} / ${agent.cost_limit_daily:.2f}
  ├── Training Score: {agent.training_score}/100
  └── Last Active: {agent.last_active.strftime('%H:%M:%S')}
"""
        
        if paused:
            report += "\n🟡 PAUSED AGENTS\n"
            report += "───────────────────────────────────────────────────────────────\n"
            for agent in paused:
                report += f"  {agent.name} ({agent.id}) - Paused\n"
        
        total_cost = sum(a.cost_today for a in self.agents.values())
        total_tasks = sum(a.tasks_completed for a in self.agents.values())
        
        report += f"""
═══════════════════════════════════════════════════════════════
SUMMARY
───────────────────────────────────────────────────────────────
Active Agents:    {len(active)}
Paused Agents:    {len(paused)}
Retired Agents:   {len(retired)}
Total Cost Today: ${total_cost:.4f}
Total Tasks:      {total_tasks}
═══════════════════════════════════════════════════════════════
"""
        
        return report
    
    async def check_auto_spawn_triggers(self, text: str) -> Optional[str]:
        """
        Check if text triggers automatic agent spawning
        
        Returns template name if triggered, None otherwise
        """
        text_lower = text.lower()
        
        for template_name, template in self.templates.items():
            for trigger in template.auto_spawn_triggers:
                if trigger in text_lower:
                    return template_name
        
        return None
    
    async def _persist_agent(self, agent: SpawnedAgent):
        """Persist agent to database"""
        # Implement with actual Supabase calls
        pass
    
    async def _update_agent(self, agent: SpawnedAgent):
        """Update agent in database"""
        # Implement with actual Supabase calls
        pass
    
    def reset_daily_costs(self):
        """Reset daily costs for all agents (called at midnight)"""
        for agent in self.agents.values():
            agent.cost_today = 0.0
            if agent.status == AgentStatus.PAUSED:
                agent.status = AgentStatus.ACTIVE


# ============================================
# TEST
# ============================================

async def test_agent_factory():
    """Test the agent factory"""
    factory = AgentFactory()
    
    print("🏭 Testing Agent Factory...\n")
    
    # Spawn some agents
    sop_agent = await factory.spawn_agent('sop-builder')
    research_agent = await factory.spawn_agent(
        'research-hunter',
        custom_name='DBA Research Hunter',
        custom_purpose='Research experience automation topics for DBA thesis'
    )
    
    # Simulate some task completions
    await factory.record_task_completion(sop_agent.id, success=True, cost=0.02)
    await factory.record_task_completion(sop_agent.id, success=True, cost=0.03)
    await factory.record_task_completion(research_agent.id, success=True, cost=0.05)
    await factory.record_task_completion(research_agent.id, success=False, cost=0.01)
    
    # Generate report
    report = await factory.generate_registry_report()
    print(report)
    
    # Test auto-spawn triggers
    trigger_text = "Can you create an SOP for the maintenance process?"
    triggered = await factory.check_auto_spawn_triggers(trigger_text)
    if triggered:
        print(f"\n🎯 Text triggered auto-spawn for: {triggered}")


if __name__ == "__main__":
    asyncio.run(test_agent_factory())
