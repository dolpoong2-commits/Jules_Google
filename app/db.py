import sqlite3
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'chat_history.db')

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_connection() as conn:
        cursor = conn.cursor()

        # Create sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                system_prompt TEXT,
                temperature REAL,
                max_tokens INTEGER
            )
        ''')

        # Create messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                role TEXT,
                content TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        ''')
        conn.commit()

def create_session(title="New Chat", system_prompt="", temperature=0.7, max_tokens=1000):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO sessions (title, system_prompt, temperature, max_tokens) VALUES (?, ?, ?, ?)''',
            (title, system_prompt, temperature, max_tokens)
        )
        conn.commit()
        return cursor.lastrowid

def get_sessions():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, title, created_at FROM sessions ORDER BY created_at DESC')
        return cursor.fetchall()

def delete_session(session_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM messages WHERE session_id = ?', (session_id,))
        cursor.execute('DELETE FROM sessions WHERE id = ?', (session_id,))
        conn.commit()

def save_message(session_id, role, content):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)''',
            (session_id, role, content)
        )
        conn.commit()

def get_messages(session_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT role, content, timestamp FROM messages WHERE session_id = ? ORDER BY timestamp ASC', (session_id,))
        return cursor.fetchall()
