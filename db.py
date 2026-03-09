import sqlite3
import json
import uuid
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = "chat_history.db"

def get_connection():
    """Returns a SQLite connection to the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database schema."""
    conn = get_connection()
    cursor = conn.cursor()

    # Create sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            title TEXT,
            model_name TEXT,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            role TEXT,
            content TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(session_id) REFERENCES sessions(session_id)
        )
    ''')

    conn.commit()
    conn.close()

def create_session(model_name: str, title: str = "New Chat", tags: str = "") -> str:
    """Creates a new session and returns the session_id."""
    session_id = str(uuid.uuid4())
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sessions (session_id, title, model_name, tags) VALUES (?, ?, ?, ?)",
        (session_id, title, model_name, tags)
    )
    conn.commit()
    conn.close()
    return session_id

def save_message(session_id: str, role: str, content: str):
    """Saves a single message to the database."""
    message_id = str(uuid.uuid4())
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (id, session_id, role, content) VALUES (?, ?, ?, ?)",
        (message_id, session_id, role, content)
    )
    conn.commit()
    conn.close()

def get_sessions() -> List[Dict[str, Any]]:
    """Retrieves all sessions."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_messages(session_id: str) -> List[Dict[str, Any]]:
    """Retrieves all messages for a specific session."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp ASC", (session_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_stats() -> Dict[str, Any]:
    """Retrieves basic database statistics."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as count FROM sessions")
    session_count = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM messages")
    message_count = cursor.fetchone()["count"]

    conn.close()
    return {
        "session_count": session_count,
        "message_count": message_count
    }

def update_session_title(session_id: str, title: str):
    """Updates the title of a session."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE sessions SET title = ? WHERE session_id = ?", (title, session_id))
    conn.commit()
    conn.close()

def update_session_tags(session_id: str, tags: str):
    """Updates the tags of a session."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE sessions SET tags = ? WHERE session_id = ?", (tags, session_id))
    conn.commit()
    conn.close()

def export_to_jsonl(filepath: str = "dataset_export.jsonl"):
    """Exports all sessions to a JSONL file formatted for OpenAI/vLLM fine-tuning."""
    sessions = get_sessions()

    with open(filepath, 'w', encoding='utf-8') as f:
        for session in sessions:
            messages = get_messages(session["session_id"])
            if not messages:
                continue

            # Format: {"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]}
            formatted_messages = []

            # Optional: You could add a system prompt based on tags/model
            system_prompt = "You are a helpful AI assistant."
            formatted_messages.append({"role": "system", "content": system_prompt})

            for msg in messages:
                # Map roles appropriately (user, assistant)
                role = "assistant" if msg["role"] == "ai" else msg["role"]
                formatted_messages.append({
                    "role": role,
                    "content": msg["content"]
                })

            json_line = json.dumps({"messages": formatted_messages}, ensure_ascii=False)
            f.write(json_line + '\n')

    return filepath

# Initialize DB on import
init_db()
