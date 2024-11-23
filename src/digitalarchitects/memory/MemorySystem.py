from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
import json
import datetime
from ..utils.logging_config import LoggerMixin
import sqlite3
from pathlib import Path

@dataclass
class MemoryEntry:
    """Base class for memory entries"""
    timestamp: float
    content: Dict[str, Any]
    importance: float = 1.0  # Higher = more important to retain
    tags: Set[str] = field(default_factory=set)
    last_accessed: float = field(default_factory=lambda: datetime.datetime.now().timestamp())

@dataclass
class ConversationMemory(MemoryEntry):
    """Stores conversation history"""
    role: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ActionMemory(MemoryEntry):
    """Stores actions taken"""
    action_type: str
    parameters: Dict[str, Any]
    result: Dict[str, Any]
    success: bool

@dataclass
class KnowledgeMemory(MemoryEntry):
    """Stores learned information"""
    category: str
    related_entities: List[str] = field(default_factory=list)
    confidence: float = 1.0

class MemoryManager(LoggerMixin):
    """Manages individual architect memory"""
    
    def __init__(self, architect_id: str, db_path: str = "memories"):
        self.architect_id = architect_id
        self.db_path = Path(db_path)
        self.db_path.mkdir(exist_ok=True)
        self.db_file = self.db_path / f"{architect_id}_memory.db"
        self.setup_database()
        
        # In-memory cache for frequently accessed memories
        self.memory_cache: Dict[str, MemoryEntry] = {}
        self.cache_size_limit = 1000  # Adjust based on needs
        
    def setup_database(self):
        """Initialize SQLite database for persistent storage"""
        with sqlite3.connect(self.db_file) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    type TEXT,
                    timestamp REAL,
                    content TEXT,
                    importance REAL,
                    tags TEXT,
                    last_accessed REAL
                )
            """)
            
    def add_memory(self, memory: MemoryEntry, memory_id: Optional[str] = None):
        """Add new memory"""
        if len(self.memory_cache) >= self.cache_size_limit:
            self._cleanup_cache()
            
        memory_id = memory_id or f"{datetime.datetime.now().timestamp()}_{id(memory)}"
        
        # Store in database
        with sqlite3.connect(self.db_file) as conn:
            conn.execute("""
                INSERT INTO memories (id, type, timestamp, content, importance, tags, last_accessed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                memory_id,
                memory.__class__.__name__,
                memory.timestamp,
                json.dumps(memory.content),
                memory.importance,
                json.dumps(list(memory.tags)),
                memory.last_accessed
            ))
        
        # Add to cache if important enough
        if memory.importance > 0.7:
            self.memory_cache[memory_id] = memory

    def get_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        """Retrieve memory by ID"""
        # Check cache first
        if memory_id in self.memory_cache:
            memory = self.memory_cache[memory_id]
            memory.last_accessed = datetime.datetime.now().timestamp()
            return memory
            
        # Check database
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.execute("""
                SELECT type, timestamp, content, importance, tags, last_accessed
                FROM memories WHERE id = ?
            """, (memory_id,))
            row = cursor.fetchone()
            
            if row:
                memory = self._create_memory_from_row(row)
                # Update last accessed time
                conn.execute("""
                    UPDATE memories SET last_accessed = ? WHERE id = ?
                """, (datetime.datetime.now().timestamp(), memory_id))
                return memory
                
        return None

    def query_memories(self, 
                      tags: Optional[Set[str]] = None,
                      importance_threshold: float = 0.0,
                      limit: int = 100) -> List[MemoryEntry]:
        """Query memories based on criteria"""
        with sqlite3.connect(self.db_file) as conn:
            query = """
                SELECT type, timestamp, content, importance, tags, last_accessed
                FROM memories
                WHERE importance >= ?
            """
            params = [importance_threshold]
            
            if tags:
                tag_list = json.dumps(list(tags))
                query += " AND tags LIKE ?"
                params.append(f"%{tag_list}%")
                
            query += " ORDER BY importance DESC LIMIT ?"
            params.append(limit)
            
            cursor = conn.execute(query, params)
            return [self._create_memory_from_row(row) for row in cursor.fetchall()]

    def _cleanup_cache(self):
        """Remove least important/accessed memories from cache"""
        if not self.memory_cache:
            return
            
        # Sort by importance and last accessed time
        sorted_memories = sorted(
            self.memory_cache.items(),
            key=lambda x: (x[1].importance, x[1].last_accessed)
        )
        
        # Remove bottom 20% of memories from cache
        memories_to_remove = len(sorted_memories) // 5
        for memory_id, _ in sorted_memories[:memories_to_remove]:
            del self.memory_cache[memory_id]

    def _create_memory_from_row(self, row) -> MemoryEntry:
        """Create appropriate memory object from database row"""
        memory_type, timestamp, content, importance, tags, last_accessed = row
        content_dict = json.loads(content)
        tags_set = set(json.loads(tags))
        
        if memory_type == "ConversationMemory":
            return ConversationMemory(
                timestamp=timestamp,
                content=content_dict,
                importance=importance,
                tags=tags_set,
                last_accessed=last_accessed,
                role=content_dict.get('role'),
                message=content_dict.get('message'),
                context=content_dict.get('context', {})
            )
        elif memory_type == "ActionMemory":
            return ActionMemory(
                timestamp=timestamp,
                content=content_dict,
                importance=importance,
                tags=tags_set,
                last_accessed=last_accessed,
                action_type=content_dict.get('action_type'),
                parameters=content_dict.get('parameters', {}),
                result=content_dict.get('result', {}),
                success=content_dict.get('success', False)
            )
        else:
            return KnowledgeMemory(
                timestamp=timestamp,
                content=content_dict,
                importance=importance,
                tags=tags_set,
                last_accessed=last_accessed,
                category=content_dict.get('category'),
                related_entities=content_dict.get('related_entities', []),
                confidence=content_dict.get('confidence', 1.0)
            )

class CollectiveMemory(LoggerMixin):
    """Manages shared memory across architects"""
    
    def __init__(self, project_id: str, db_path: str = "collective_memories"):
        self.project_id = project_id
        self.db_path = Path(db_path)
        self.db_path.mkdir(exist_ok=True)
        self.db_file = self.db_path / f"{project_id}_collective.db"
        self.setup_database()
        
    def setup_database(self):
        """Initialize collective memory database"""
        with sqlite3.connect(self.db_file) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS collective_memories (
                    id TEXT PRIMARY KEY,
                    category TEXT,
                    content TEXT,
                    contributors TEXT,
                    last_modified REAL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS architect_roles (
                    architect_id TEXT PRIMARY KEY,
                    role TEXT,
                    responsibilities TEXT,
                    active_tasks TEXT
                )
            """)

    def add_collective_knowledge(self, 
                               category: str,
                               content: Dict[str, Any],
                               contributor_id: str):
        """Add shared knowledge"""
        memory_id = f"{category}_{datetime.datetime.now().timestamp()}"
        
        with sqlite3.connect(self.db_file) as conn:
            existing = conn.execute("""
                SELECT contributors FROM collective_memories
                WHERE category = ? AND id = ?
            """, (category, memory_id)).fetchone()
            
            if existing:
                contributors = set(json.loads(existing[0]))
                contributors.add(contributor_id)
                
                conn.execute("""
                    UPDATE collective_memories
                    SET content = ?, contributors = ?, last_modified = ?
                    WHERE category = ? AND id = ?
                """, (
                    json.dumps(content),
                    json.dumps(list(contributors)),
                    datetime.datetime.now().timestamp(),
                    category,
                    memory_id
                ))
            else:
                conn.execute("""
                    INSERT INTO collective_memories (id, category, content, contributors, last_modified)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    memory_id,
                    category,
                    json.dumps(content),
                    json.dumps([contributor_id]),
                    datetime.datetime.now().timestamp()
                ))

    def update_architect_role(self,
                            architect_id: str,
                            role: str,
                            responsibilities: List[str],
                            active_tasks: List[Dict[str, Any]]):
        """Update architect's role and responsibilities"""
        with sqlite3.connect(self.db_file) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO architect_roles (architect_id, role, responsibilities, active_tasks)
                VALUES (?, ?, ?, ?)
            """, (
                architect_id,
                role,
                json.dumps(responsibilities),
                json.dumps(active_tasks)
            ))

    def get_architect_roles(self) -> Dict[str, Dict[str, Any]]:
        """Get all architects' roles"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.execute("SELECT * FROM architect_roles")
            return {
                row[0]: {
                    'role': row[1],
                    'responsibilities': json.loads(row[2]),
                    'active_tasks': json.loads(row[3])
                }
                for row in cursor.fetchall()
            }