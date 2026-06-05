# utils/memory.py
"""
Persistent AI Memory — Feature #7
Uses SQLite to remember employee interactions across sessions.
No external services required.
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional
from loguru import logger


class MemoryEngine:
    def __init__(self, db_path: str = "./hr_ai.db", max_entries: int = 50):
        self.db_path = db_path
        self.max_entries = max_entries
        self._init_tables()

    def _init_tables(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL, session_id TEXT NOT NULL,
            intent TEXT, agent TEXT, response TEXT, timestamp TEXT NOT NULL)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS employee_context (
            employee_id TEXT PRIMARY KEY, last_action TEXT, manager_name TEXT,
            preferred_lang TEXT DEFAULT 'en', leave_balance TEXT, last_updated TEXT)""")
        conn.commit(); conn.close()

    def save_interaction(self, employee_id: str, session_id: str, intent: str, agent: str, response: str):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("INSERT INTO memory (employee_id,session_id,intent,agent,response,timestamp) VALUES (?,?,?,?,?,?)",
                (employee_id, session_id, intent, agent, response[:500], datetime.now().isoformat()))
            conn.commit(); conn.close()
        except Exception as e:
            logger.error(f"Memory save failed: {e}")

    def get_history(self, employee_id: str, limit: int = 10) -> list:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("SELECT intent,agent,response,timestamp FROM memory WHERE employee_id=? ORDER BY id DESC LIMIT ?",
                (employee_id, limit))
            rows = [{"intent":r[0],"agent":r[1],"response":r[2],"timestamp":r[3]} for r in cursor.fetchall()]
            conn.close(); return rows
        except: return []

    def get_context(self, employee_id: str) -> dict:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("SELECT * FROM employee_context WHERE employee_id=?", (employee_id,))
            row = cursor.fetchone(); conn.close()
            if row:
                return {"employee_id":row[0],"last_action":row[1],"manager_name":row[2],
                        "preferred_lang":row[3],"leave_balance":json.loads(row[4]) if row[4] else {},"last_updated":row[5]}
        except: pass
        return {}

    def update_context(self, employee_id: str, **kwargs):
        try:
            existing = self.get_context(employee_id)
            conn = sqlite3.connect(self.db_path)
            kwargs["last_updated"] = datetime.now().isoformat()
            if existing:
                fields = ", ".join(f"{k}=?" for k in kwargs)
                conn.execute(f"UPDATE employee_context SET {fields} WHERE employee_id=?",
                    list(kwargs.values()) + [employee_id])
            else:
                fields = ", ".join(kwargs.keys())
                placeholders = ", ".join("?" * len(kwargs))
                conn.execute(f"INSERT INTO employee_context (employee_id,{fields}) VALUES (?,{placeholders})",
                    [employee_id] + list(kwargs.values()))
            conn.commit(); conn.close()
        except Exception as e:
            logger.error(f"Context update failed: {e}")

memory_engine = MemoryEngine()
