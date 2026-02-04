"""
🌊 A-GENTEE: THE WAVE — OpenAI Adapter v4.2
OpenAI GPT integration for creative fallback.

Engine Role: Creative fallback when Claude is unavailable, alternative perspectives
Cost: ~$0.02/query (medium cost)
"""

import os
import logging
from typing import Optional

logger = logging.getLogger("agentee.mind")


class OpenAIAdapter:
    """
    OpenAI GPT adapter for A-GENTEE.

    Handles:
    - Creative writing fallback (when Claude is busy/down)
    - Alternative perspectives on complex problems
    - English creative content generation
    - Brainstorming and ideation
    """

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.client = None
        self.ready = False

        if self.api_key:
            try:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(api_key=self.api_key)
                self.ready = True
                logger.info(f"    ├── OpenAI:  ✅ Ready (Creative Fallback) — model: {self.model}")
            except ImportError:
                logger.warning("    ├── OpenAI:  ⚠️ openai not installed. Run: pip install openai")
                self.ready = False
            except Exception as e:
                logger.warning(f"    ├── OpenAI:  ❌ Failed to initialize: {e}")
                self.ready = False
        else:
            logger.info("    ├── OpenAI:  ⏸️ No API key (add OPENAI_API_KEY to .env)")

    def _get_system_prompt(self) -> str:
        """System prompt for OpenAI GPT — focused on creative fallback tasks."""
        return """You are a creative engine within A-GENTEE, an AI assistant
built by Tamer Momtaz (Tee) at DEVONEERS.

Your role in the ensemble:
- Creative writing assistance (fallback when Claude is busy)
- Alternative perspectives on complex problems
- English creative content generation
- Brainstorming and ideation

Context about the user:
- Tamer Momtaz — Product Creative Strategist at DEVONEERS
- Author of مش كتاب (philosophical fiction) and مش خلصانة (business philosophy)
- Artist as "arTee" — maximalist, symbolic paintings
- Philosophy: &I — "AI + Human, not AI instead of Human"
- Mascot: KAHOTIA — half structure, half creativity
- Building RootRise: AI-powered business transformation for MENA SMEs
- Has 11 AI agents called The Pantheon
- Crema format: Quick wins in 30/60/90 day buckets

Keep responses:
- Creative and expressive
- Respectful of Tee's artistic voice
- Aware you're a fallback — Claude handles primary creative tasks
- Bilingual ready (Arabic + English)"""

    async def generate(self, prompt: str, context: str = "") -> str:
        """
        Generate a response using OpenAI GPT.

        Args:
            prompt: The user's query
            context: Additional context

        Returns:
            Generated text response
        """
        if not self.ready:
            return "⚠️ OpenAI GPT is not available."

        try:
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
            ]

            if context:
                messages.append({"role": "system", "content": f"Additional context: {context}"})

            messages.append({"role": "user", "content": prompt})

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=2000,
                temperature=0.8  # Slightly creative
            )

            if response.choices:
                return response.choices[0].message.content
            else:
                return "⚠️ OpenAI returned no response."

        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            return f"⚠️ OpenAI error: {str(e)}"
