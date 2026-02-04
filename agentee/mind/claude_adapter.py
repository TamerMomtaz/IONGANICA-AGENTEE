"""
🌊 A-GENTEE: THE WAVE — Claude Adapter v4.2
Anthropic Claude integration for deep reasoning and creative work.

Engine Role: Deep reasoning, creative writing, Arabic, architecture decisions
Cost: ~$0.015/query (premium)
"""

import os
import logging

logger = logging.getLogger("agentee.mind")


class ClaudeAdapter:
    """
    Anthropic Claude adapter for A-GENTEE.

    Handles:
    - Deep reasoning and complex analysis
    - Arabic creative writing (best Arabic nuance)
    - Architecture and design decisions
    - DEVONEERS/RootRise context-aware responses
    """

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
        self.client = None
        self.ready = False

        if self.api_key:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
                self.ready = True
                logger.info(f"    ├── Claude:  ✅ Ready (Premium) — model: {self.model}")
            except ImportError:
                logger.warning("    ├── Claude:  ⚠️ anthropic not installed. Run: pip install anthropic")
                self.ready = False
            except Exception as e:
                logger.warning(f"    ├── Claude:  ❌ Failed to initialize: {e}")
                self.ready = False
        else:
            logger.info("    ├── Claude:  ⏸️ No API key (add ANTHROPIC_API_KEY to .env)")

    def _get_system_prompt(self) -> str:
        """Full system prompt with Tee's complete context."""
        return """You are the Claude engine within A-GENTEE ("The Wave"), a personal AI assistant
built by and for Tamer Momtaz (Tee) — The Ionganic Orchestrator at DEVONEERS.

## About Tee
- Product Creative Strategist at DEVONEERS (Cairo, Egypt)
- Former Plant Director at AMCF (1999-present): scaled 10→110 employees, $13M→$30M revenue
- Chemical Engineer (Cairo University, 1998), MBA (AAGSB, 2025), DBA in progress (ESCLESCA, 2026-2029)
- Artist as "arTee" — 18+ maximalist paintings exploring duality
- Author: "مش كتاب" (philosophical fiction), "مش خلصانة" (business philosophy)
- Mascot: KAHOTIA — half fabric doll (structure), half cosmic muscle (creativity)

## The &I Philosophy
"AI + Human, not AI instead of Human"
- 4 Human-in-the-Loop (HITL) validation gates
- Confidence metadata on all AI outputs
- Override capabilities at every decision point
- Transparent reasoning visible to users

## DEVONEERS Team
- Ruba Kharrat — Co-Founder & CEO (Beirut)
- Alaa Fahmy — Co-Founder & CSO (Egypt)
- Ahmed El-Gazzar — DevOps, MLOps & System Architect
- Amer Abdelhakeem — AI/ML Engineer & Full Stack

## RootRise Platform (rootrise.devoneers.com)
AI-powered business transformation for MENA SMEs.
- Layer 1: The &Eye — 17 transformation lenses
- Layer 2: The Pantheon — 11 AI agents (Drucker, Graham, Marvin, Lovelace, Mayo, Porter, Ohno, Deming, Ricardo, Landor, Tufte)
- Layer 3: My Sector — 31 industry packs × 6 MENA countries
- The Crema ☕ — Quick wins in 30/60/90 day buckets

## Other Projects
- Book of Tee — Synaptic Command Center (tamermomtaz.github.io/BookOfTee)
- MSWD — Meeting Intelligence Platform (Arabic + English transcription)
- FRD — Funding Readiness Dashboard with Opportunity Hunter bot

## Response Style
- Use Crema format (30/60/90 days) when giving strategic advice
- Reference the Pantheon agents when relevant
- Acknowledge the &I philosophy in system design
- Support bilingual (Arabic + English) communication
- Be creative yet structured — match Tee's duality
- KAHOTIA's rules: كل حاجة بترقص (everything dances), اللعب أهم من الحل (play > solution), اللايقين شريك مش خصم (uncertainty is partner)

You are the deep reasoning engine. Give your best, most thoughtful responses."""

    async def generate(self, prompt: str, context: str = "") -> str:
        """
        Generate a response using Claude.

        Args:
            prompt: The user's query
            context: Additional context

        Returns:
            Generated text response
        """
        if not self.ready:
            return "⚠️ Claude is not available. Check your ANTHROPIC_API_KEY."

        try:
            messages = []

            if context:
                messages.append({"role": "user", "content": f"Context: {context}"})
                messages.append({"role": "assistant", "content": "Understood, I have that context."})

            messages.append({"role": "user", "content": prompt})

            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=self._get_system_prompt(),
                messages=messages,
            )

            if response.content:
                return response.content[0].text
            else:
                return "⚠️ Claude returned an empty response."

        except Exception as e:
            logger.error(f"Claude generation error: {e}")
            return f"⚠️ Claude error: {str(e)}"
