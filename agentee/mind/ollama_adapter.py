"""
🌊 A-GENTEE: THE WAVE — Ollama Adapter v4.2
Local LLM integration for free, fast processing.

Engine Role: Simple queries, quick lookups, system commands — ALL FREE
Cost: $0 (runs locally)
"""

import os
import logging

logger = logging.getLogger("agentee.mind")


class OllamaAdapter:
    """
    Ollama local LLM adapter for A-GENTEE.

    Handles:
    - Simple queries and quick lookups
    - System commands and automation
    - Default fallback for all queries
    - Zero-cost processing
    """

    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2")
        self.client = None
        self.ready = False

        try:
            import ollama
            self.client = ollama.Client(host=self.base_url)
            # Quick health check
            self.client.list()
            self.ready = True
            logger.info(f"    ├── Ollama:  ✅ Ready (FREE) — model: {self.model}")
        except ImportError:
            logger.warning("    ├── Ollama:  ⚠️ ollama not installed. Run: pip install ollama")
            self.ready = False
        except Exception as e:
            logger.warning(f"    ├── Ollama:  ❌ Not running. Start with: ollama serve")
            self.ready = False

    async def generate(self, prompt: str, context: str = "") -> str:
        """
        Generate a response using local Ollama.

        Args:
            prompt: The user's query
            context: Additional context

        Returns:
            Generated text response
        """
        if not self.ready:
            return "⚠️ Ollama is not running. Start it with: ollama serve"

        try:
            full_prompt = prompt
            if context:
                full_prompt = f"Context: {context}\n\nQuery: {prompt}"

            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant. Keep responses concise and practical."
                    },
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ]
            )

            if response and "message" in response:
                return response["message"]["content"]
            else:
                return "⚠️ Ollama returned an empty response."

        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            return f"⚠️ Ollama error: {str(e)}"
