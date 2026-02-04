"""
🌊 A-GENTEE: THE WAVE — Gemini Adapter v4.2
Google Gemini integration using the NEW google-genai SDK.

MIGRATED from deprecated google-generativeai → google-genai
The old SDK (google.generativeai) reached end-of-life Nov 30, 2025.
The new SDK (google.genai) is the official replacement.

Engine Role: Data processing, research synthesis, cost-effective reasoning
Cost: ~$0.001/query (cheapest cloud option)
"""

import os
import logging
from typing import Optional

logger = logging.getLogger("agentee.mind")


class GeminiAdapter:
    """
    Google Gemini adapter for A-GENTEE.
    Uses the NEW google-genai SDK (not the deprecated google-generativeai).

    Handles:
    - Data analysis and processing
    - Research synthesis and summarization
    - Fact-finding and information extraction
    - Cost-effective reasoning (cheaper than Claude)
    """

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.client = None
        self.ready = False

        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                self.ready = True
                logger.info(f"    ├── Gemini:  ✅ Ready (Data Engine) — model: {self.model_name}")
            except ImportError:
                logger.warning("    ├── Gemini:  ⚠️ google-genai not installed. Run: pip install google-genai")
                self.ready = False
            except Exception as e:
                logger.warning(f"    ├── Gemini:  ❌ Failed to initialize: {e}")
                self.ready = False
        else:
            logger.info("    ├── Gemini:  ⏸️ No API key (add GEMINI_API_KEY to .env)")

    def _get_system_prompt(self) -> str:
        """System prompt for Gemini — focused on data and research tasks."""
        return """You are a data analysis and research engine within A-GENTEE,
an AI assistant system built by Tamer Momtaz (Tee) at DEVONEERS.

Your role in the ensemble:
- Data analysis and processing
- Research synthesis and summarization
- Fact-finding and information extraction
- Cost-effective reasoning for medium-complexity tasks

Context about the user:
- Tamer Momtaz — Product Creative Strategist at DEVONEERS
- Building RootRise: AI-powered business transformation for MENA SMEs
- Philosophy: &I — "AI + Human, not AI instead of Human"
- Working across: tech, factory operations, creative writing, DBA studies
- Has 11 AI agents called The Pantheon (Drucker, Graham, Porter, etc.)
- Crema format: Quick wins in 30/60/90 day buckets

Keep responses:
- Data-focused and precise
- Well-structured with clear findings
- Efficient — you're the cost-effective engine
- Bilingual ready (Arabic + English)

You are part of the A-GENTEE ensemble alongside Claude (deep reasoning),
Ollama (simple/free queries), and OpenAI GPT (creative fallback)."""

    async def generate(self, prompt: str, context: str = "") -> str:
        """
        Generate a response using Gemini via the new google-genai SDK.

        Args:
            prompt: The user's query
            context: Additional context from the system

        Returns:
            Generated text response
        """
        if not self.ready:
            return "⚠️ Gemini is not available. Falling back to another engine."

        try:
            full_prompt = prompt
            if context:
                full_prompt = f"Context: {context}\n\nQuery: {prompt}"

            # New SDK: client.models.generate_content()
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config={
                    "system_instruction": self._get_system_prompt(),
                    "max_output_tokens": 2000,
                    "temperature": 0.4,  # More factual for data tasks
                }
            )

            if response and response.text:
                return response.text
            else:
                return "⚠️ Gemini returned an empty response."

        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            return f"⚠️ Gemini error: {str(e)}"

    async def analyze_data(self, data: str, instruction: str = "Analyze this data") -> str:
        """Specialized data analysis method."""
        prompt = f"""{instruction}

Data:
{data}

Provide:
1. Key findings
2. Patterns detected
3. Actionable insights
4. Any anomalies or concerns"""
        return await self.generate(prompt)

    async def research(self, topic: str) -> str:
        """Research synthesis on a topic."""
        prompt = f"""Research and synthesize information on: {topic}

Structure your response as:
1. Overview
2. Key facts and data points
3. Current trends
4. Relevance to MENA business ecosystem
5. Actionable takeaways"""
        return await self.generate(prompt)

    async def summarize(self, content: str, style: str = "concise") -> str:
        """Summarize content efficiently."""
        style_instructions = {
            "concise": "Provide a brief 2-3 sentence summary.",
            "detailed": "Provide a comprehensive summary with key details.",
            "bullet": "Provide a bullet-point summary of key takeaways."
        }
        instruction = style_instructions.get(style, style_instructions["concise"])
        prompt = f"""{instruction}

Content to summarize:
{content}"""
        return await self.generate(prompt)
