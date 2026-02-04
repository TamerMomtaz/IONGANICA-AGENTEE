"""
🌊 A-GENTEE: THE WAVE — Core
The main entry point. The Wave awakens here.

"أنا الموجة... دايماً هنا، دايماً بسمع، دايماً جاهز"
"I am The Wave... Always here, always listening, always ready"
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Load environment variables
load_dotenv()

# Configure loguru
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    "data/logs/agentee_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="30 days",
    level="DEBUG"
)

# Rich console for beautiful output
console = Console()


class AGentee:
    """
    🌊 A-GENTEE: THE WAVE
    The omnipresent AI assistant for Tee (Tamer Momtaz)
    """
    
    def __init__(self):
        logger.info("🌊 A-GENTEE initializing... The Wave awakens.")
        self.start_time = datetime.now()
        self.mind = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize all components"""
        logger.info("🌊 Initializing components...")
        
        # Ensure data directories exist
        Path("data/logs").mkdir(parents=True, exist_ok=True)
        Path("data").mkdir(parents=True, exist_ok=True)
        
        # Initialize The Mind (Ensemble Brain)
        try:
            from agentee.mind import Mind
            self.mind = Mind()
            logger.info("🌊 Mind component: ✅ Active")
        except Exception as e:
            logger.error(f"🌊 Mind component failed: {e}")
            self.mind = None
        
        self.initialized = True
        logger.info("🌊 A-GENTEE ready. The Wave is listening.")
    
    async def process_input(self, user_input: str) -> str:
        """Process user input through the ensemble brain"""
        
        # Built-in commands
        if user_input.lower() in ['exit', 'quit', 'bye', 'خلاص', 'سلام']:
            return "__EXIT__"
        
        if user_input.lower() == 'stats':
            if self.mind:
                return self.mind.get_stats()
            return "Mind not initialized — no stats available."
        
        if user_input.lower() == 'status':
            return self._get_status()
        
        # Process through Mind
        if self.mind:
            return await self.mind.think(user_input)
        else:
            return "⚠️ Mind component not initialized. Check your API keys and Ollama."
    
    def _get_status(self) -> str:
        """Get system status"""
        uptime = datetime.now() - self.start_time
        minutes = int(uptime.total_seconds() / 60)
        
        status_lines = [
            f"🌊 A-GENTEE Status",
            f"  Uptime:    {minutes} minutes",
            f"  Mind:      {'✅ Active' if self.mind else '❌ Inactive'}",
        ]
        
        if self.mind:
            status_lines.append(f"  Ollama:    {'✅ Ready (FREE)' if self.mind.ollama.is_available() else '❌ Offline'}")
            status_lines.append(f"  Claude:    {'✅ Ready' if self.mind.claude.is_available() else '❌ Offline'}")
        
        return "\n".join(status_lines)
    
    async def start(self):
        """Start the interactive loop"""
        
        # Display welcome banner
        banner = Text()
        banner.append("  🌊  A-GENTEE: THE WAVE  🌊\n\n", style="bold cyan")
        banner.append('  "أنا الموجة... دايماً هنا، دايماً بسمع"\n', style="italic")
        banner.append('  "I am The Wave... Always here, always listening"\n\n', style="italic dim")
        banner.append("  Status: ", style="bold")
        banner.append("ACTIVE\n", style="bold green")
        banner.append("\n  Commands: stats | status | exit\n", style="dim")
        banner.append('  Or just talk to me naturally 🌊', style="dim")
        
        console.print(Panel(banner, border_style="cyan", padding=(1, 2)))
        
        # Main loop
        while True:
            try:
                user_input = console.input("\n[cyan]🌊 > [/cyan]").strip()
                
                if not user_input:
                    continue
                
                response = await self.process_input(user_input)
                
                if response == "__EXIT__":
                    console.print("\n[cyan]🌊 The Wave rests... but never disappears. مع السلامة[/cyan]\n")
                    break
                
                # Display response
                console.print(f"\n[bold cyan]🌊[/bold cyan] {response}")
                
            except KeyboardInterrupt:
                console.print("\n\n[cyan]🌊 The Wave rests... Ctrl+C detected. مع السلامة[/cyan]\n")
                break
            except EOFError:
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                console.print(f"\n[red]⚠️ Error: {e}[/red]")


async def main():
    """Main entry point"""
    wave = AGentee()
    await wave.initialize()
    await wave.start()


if __name__ == "__main__":
    asyncio.run(main())
