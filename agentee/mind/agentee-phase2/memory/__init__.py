"""
💾 THE MEMORY — A-GENTEE Storage Layer v1.0
"أنا الموجة... بفتكر كل حاجة، بتعلم كل يوم"
"I am The Wave... I remember everything, I learn every day"

Two-tier memory architecture:
1. HOT MEMORY (SQLite local) — Fast, current session, 24h cache
2. COLD MEMORY (Supabase REST) — Cloud, historical, cross-device sync

What A-GENTEE remembers:
- Conversations (who said what, when)
- Ideas (extracted from conversations)
- Preferences (Tee's likes, style, patterns)
- Context (current projects, tasks, moods)
- Learning (what was taught, by whom)
"""

import os
import json
import sqlite3
import asyncio
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

load_dotenv()


class TheMemory:
    """
    A-GENTEE's storage layer — remembers across sessions.
    
    Hot Memory: SQLite (local, fast, current context)
    Cold Memory: Supabase REST API (cloud, persistent, cross-device)
    """

    VERSION = "1.0"

    def __init__(self, db_path: str = None):
        # Hot memory (local SQLite)
        if db_path is None:
            project_root = Path(__file__).parent.parent.parent
            db_path = str(project_root / "data" / "local_memory.db")
        
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Cold memory (Supabase)
        self.supabase_url = os.getenv("SUPABASE_URL", "")
        self.supabase_key = os.getenv("SUPABASE_KEY", "")
        self.supabase_ready = bool(self.supabase_url and self.supabase_key)
        
        # Stats
        self.stats = {
            "hot_writes": 0,
            "hot_reads": 0,
            "cold_writes": 0,
            "cold_reads": 0,
            "conversations_stored": 0,
            "ideas_stored": 0,
            "preferences_stored": 0,
        }
        
        # Initialize hot memory
        self._init_hot_memory()

    def _init_hot_memory(self):
        """Create SQLite tables for hot memory."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Conversations table
        c.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                speaker TEXT DEFAULT 'tee',
                language TEXT DEFAULT 'en',
                query TEXT,
                response TEXT,
                engine TEXT,
                category TEXT,
                tags TEXT DEFAULT '[]',
                session_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Ideas table (extracted from conversations)
        c.execute("""
            CREATE TABLE IF NOT EXISTS ideas (
                id TEXT PRIMARY KEY,
                source_conversation_id TEXT,
                idea TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                potential_score INTEGER DEFAULT 5,
                status TEXT DEFAULT 'raw',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_conversation_id) REFERENCES conversations(id)
            )
        """)
        
        # Preferences (Tee's patterns, likes, style)
        c.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                confidence REAL DEFAULT 0.5,
                source TEXT DEFAULT 'observed',
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Context (current state, active projects, mood)
        c.execute("""
            CREATE TABLE IF NOT EXISTS context (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                expires_at TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Learning log
        c.execute("""
            CREATE TABLE IF NOT EXISTS learning_log (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                source TEXT,
                domain TEXT,
                content_summary TEXT,
                model_used TEXT,
                cost REAL DEFAULT 0.0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Session tracking
        c.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                queries_count INTEGER DEFAULT 0,
                engines_used TEXT DEFAULT '{}',
                total_cost REAL DEFAULT 0.0
            )
        """)
        
        conn.commit()
        conn.close()

    def get_status(self) -> dict:
        """Return memory system status."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        counts = {}
        for table in ["conversations", "ideas", "preferences", "context", "learning_log", "sessions"]:
            c.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = c.fetchone()[0]
        
        conn.close()
        
        return {
            "version": self.VERSION,
            "hot_memory": {
                "path": self.db_path,
                "tables": counts,
            },
            "cold_memory": {
                "supabase": "✅ Configured" if self.supabase_ready else "❌ Not configured",
                "url": self.supabase_url[:30] + "..." if self.supabase_url else "N/A",
            },
            "stats": self.stats,
        }

    # ═══════════════════════════════════════════
    # CONVERSATION MEMORY
    # ═══════════════════════════════════════════

    def store_conversation(self, query: str, response: str, engine: str = "",
                           category: str = "", language: str = "en",
                           tags: list = None, session_id: str = "") -> str:
        """Store a conversation exchange."""
        conv_id = self._generate_id(f"{query}{datetime.now().isoformat()}")
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("""
            INSERT INTO conversations (id, timestamp, speaker, language, query, 
                                       response, engine, category, tags, session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            conv_id,
            datetime.now().isoformat(),
            "tee",
            language,
            query,
            response,
            engine,
            category,
            json.dumps(tags or []),
            session_id,
        ))
        
        conn.commit()
        conn.close()
        
        self.stats["hot_writes"] += 1
        self.stats["conversations_stored"] += 1
        
        return conv_id

    def get_recent_conversations(self, limit: int = 10, 
                                  category: str = None) -> List[Dict]:
        """Retrieve recent conversations."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        if category:
            c.execute("""
                SELECT * FROM conversations 
                WHERE category = ? 
                ORDER BY timestamp DESC LIMIT ?
            """, (category, limit))
        else:
            c.execute("""
                SELECT * FROM conversations 
                ORDER BY timestamp DESC LIMIT ?
            """, (limit,))
        
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        
        self.stats["hot_reads"] += 1
        return rows

    def search_conversations(self, query: str, limit: int = 5) -> List[Dict]:
        """Search conversations by content."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("""
            SELECT * FROM conversations 
            WHERE query LIKE ? OR response LIKE ?
            ORDER BY timestamp DESC LIMIT ?
        """, (f"%{query}%", f"%{query}%", limit))
        
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        
        self.stats["hot_reads"] += 1
        return rows

    # ═══════════════════════════════════════════
    # IDEAS MEMORY
    # ═══════════════════════════════════════════

    def store_idea(self, idea: str, category: str = "general",
                   potential_score: int = 5, source_conv_id: str = None) -> str:
        """Store an idea extracted from conversation."""
        idea_id = self._generate_id(f"idea-{idea}{datetime.now().isoformat()}")
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("""
            INSERT INTO ideas (id, source_conversation_id, idea, category, 
                              potential_score, status)
            VALUES (?, ?, ?, ?, ?, 'raw')
        """, (idea_id, source_conv_id, idea, category, potential_score))
        
        conn.commit()
        conn.close()
        
        self.stats["hot_writes"] += 1
        self.stats["ideas_stored"] += 1
        
        return idea_id

    def get_ideas(self, category: str = None, status: str = None,
                  limit: int = 20) -> List[Dict]:
        """Get stored ideas."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        query = "SELECT * FROM ideas WHERE 1=1"
        params = []
        
        if category:
            query += " AND category = ?"
            params.append(category)
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY potential_score DESC, created_at DESC LIMIT ?"
        params.append(limit)
        
        c.execute(query, params)
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        
        self.stats["hot_reads"] += 1
        return rows

    # ═══════════════════════════════════════════
    # PREFERENCES MEMORY
    # ═══════════════════════════════════════════

    def set_preference(self, key: str, value: str, category: str = "general",
                       confidence: float = 0.5, source: str = "observed"):
        """Store or update a preference."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("""
            INSERT OR REPLACE INTO preferences (key, value, category, confidence, 
                                                 source, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (key, value, category, confidence, source, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        self.stats["hot_writes"] += 1
        self.stats["preferences_stored"] += 1

    def get_preference(self, key: str) -> Optional[str]:
        """Get a preference value."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("SELECT value FROM preferences WHERE key = ?", (key,))
        row = c.fetchone()
        conn.close()
        
        self.stats["hot_reads"] += 1
        return row[0] if row else None

    def get_all_preferences(self, category: str = None) -> Dict[str, str]:
        """Get all preferences, optionally filtered by category."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        if category:
            c.execute("SELECT * FROM preferences WHERE category = ?", (category,))
        else:
            c.execute("SELECT * FROM preferences")
        
        result = {row["key"]: dict(row) for row in c.fetchall()}
        conn.close()
        
        self.stats["hot_reads"] += 1
        return result

    # ═══════════════════════════════════════════
    # CONTEXT MEMORY (short-term, expires)
    # ═══════════════════════════════════════════

    def set_context(self, key: str, value: str, ttl_hours: int = 24):
        """Set a context value with expiration."""
        expires = (datetime.now() + timedelta(hours=ttl_hours)).isoformat()
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("""
            INSERT OR REPLACE INTO context (key, value, expires_at, updated_at)
            VALUES (?, ?, ?, ?)
        """, (key, value, expires, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        self.stats["hot_writes"] += 1

    def get_context(self, key: str) -> Optional[str]:
        """Get a context value (returns None if expired)."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("""
            SELECT value, expires_at FROM context WHERE key = ?
        """, (key,))
        
        row = c.fetchone()
        conn.close()
        
        if row is None:
            return None
        
        value, expires_at = row
        if expires_at and datetime.fromisoformat(expires_at) < datetime.now():
            # Expired — clean up
            self._delete_context(key)
            return None
        
        self.stats["hot_reads"] += 1
        return value

    def _delete_context(self, key: str):
        """Remove expired context."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM context WHERE key = ?", (key,))
        conn.commit()
        conn.close()

    # ═══════════════════════════════════════════
    # LEARNING LOG
    # ═══════════════════════════════════════════

    def log_learning(self, source: str, domain: str, summary: str,
                     model_used: str = "", cost: float = 0.0) -> str:
        """Log a learning event."""
        log_id = self._generate_id(f"learn-{datetime.now().isoformat()}")
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("""
            INSERT INTO learning_log (id, timestamp, source, domain, 
                                      content_summary, model_used, cost)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (log_id, datetime.now().isoformat(), source, domain,
              summary, model_used, cost))
        
        conn.commit()
        conn.close()
        
        self.stats["hot_writes"] += 1
        return log_id

    # ═══════════════════════════════════════════
    # SESSION MANAGEMENT
    # ═══════════════════════════════════════════

    def start_session(self) -> str:
        """Create a new session."""
        session_id = self._generate_id(f"session-{datetime.now().isoformat()}")
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("""
            INSERT INTO sessions (id, started_at)
            VALUES (?, ?)
        """, (session_id, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return session_id

    def end_session(self, session_id: str, queries_count: int = 0,
                    engines_used: dict = None, total_cost: float = 0.0):
        """Close a session with stats."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("""
            UPDATE sessions 
            SET ended_at = ?, queries_count = ?, engines_used = ?, total_cost = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), queries_count,
              json.dumps(engines_used or {}), total_cost, session_id))
        
        conn.commit()
        conn.close()

    # ═══════════════════════════════════════════
    # COLD MEMORY (Supabase REST)
    # ═══════════════════════════════════════════

    async def sync_to_cold(self, table: str, data: dict) -> bool:
        """Push data to Supabase cold storage via REST API."""
        if not self.supabase_ready:
            return False
        
        try:
            import httpx
            
            url = f"{self.supabase_url}/rest/v1/{table}"
            headers = {
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=data)
                
                if response.status_code in (200, 201):
                    self.stats["cold_writes"] += 1
                    return True
                else:
                    print(f"    ⚠️ Supabase write failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"    ⚠️ Supabase error: {e}")
            return False

    async def read_from_cold(self, table: str, query_params: dict = None) -> List[Dict]:
        """Read data from Supabase cold storage."""
        if not self.supabase_ready:
            return []
        
        try:
            import httpx
            
            url = f"{self.supabase_url}/rest/v1/{table}"
            headers = {
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}",
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=query_params)
                
                if response.status_code == 200:
                    self.stats["cold_reads"] += 1
                    return response.json()
                else:
                    return []
                    
        except Exception as e:
            print(f"    ⚠️ Supabase read error: {e}")
            return []

    # ═══════════════════════════════════════════
    # CONTEXT BUILDER (for Mind prompts)
    # ═══════════════════════════════════════════

    def build_context_prompt(self, max_conversations: int = 5) -> str:
        """
        Build a context string for the Mind's system prompt.
        Includes recent conversations, active preferences, and current context.
        """
        parts = []
        
        # Recent conversations
        recent = self.get_recent_conversations(limit=max_conversations)
        if recent:
            parts.append("=== RECENT CONVERSATION HISTORY ===")
            for conv in recent:
                parts.append(f"[{conv['timestamp'][:16]}] Tee: {conv['query'][:100]}")
                parts.append(f"  → A-GENTEE ({conv['engine']}): {conv['response'][:100]}")
            parts.append("")
        
        # Active preferences
        prefs = self.get_all_preferences()
        if prefs:
            parts.append("=== TEE'S KNOWN PREFERENCES ===")
            for key, pref in prefs.items():
                parts.append(f"  {key}: {pref['value']}")
            parts.append("")
        
        # Current context
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            SELECT key, value FROM context 
            WHERE expires_at > ? OR expires_at IS NULL
        """, (datetime.now().isoformat(),))
        ctx = c.fetchall()
        conn.close()
        
        if ctx:
            parts.append("=== CURRENT CONTEXT ===")
            for key, value in ctx:
                parts.append(f"  {key}: {value}")
            parts.append("")
        
        return "\n".join(parts)

    # ═══════════════════════════════════════════
    # UTILITIES
    # ═══════════════════════════════════════════

    def _generate_id(self, seed: str) -> str:
        """Generate a short unique ID."""
        return hashlib.sha256(seed.encode()).hexdigest()[:16]

    def cleanup_expired(self):
        """Remove expired context entries."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            DELETE FROM context 
            WHERE expires_at IS NOT NULL AND expires_at < ?
        """, (datetime.now().isoformat(),))
        deleted = c.rowcount
        conn.commit()
        conn.close()
        return deleted


# Quick test
if __name__ == "__main__":
    memory = TheMemory()
    status = memory.get_status()
    
    print("💾 THE MEMORY Status:")
    print(f"    Hot Memory: {status['hot_memory']['path']}")
    print(f"    Tables: {status['hot_memory']['tables']}")
    print(f"    Cold Memory: {status['cold_memory']['supabase']}")
    
    # Test storing
    conv_id = memory.store_conversation(
        query="Hello A-GENTEE",
        response="Hello Tee! The Wave is listening.",
        engine="ollama",
        category="greeting",
    )
    print(f"\n    Stored conversation: {conv_id}")
    
    # Test retrieval
    recent = memory.get_recent_conversations(limit=3)
    print(f"    Recent conversations: {len(recent)}")
    
    # Test preferences
    memory.set_preference("voice_mode", "default", "voice", 0.9, "explicit")
    pref = memory.get_preference("voice_mode")
    print(f"    Preference 'voice_mode': {pref}")
    
    print("\n    ✅ Memory system working!")
