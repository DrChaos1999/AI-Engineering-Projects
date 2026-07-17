# ==========================================================
# File : database.py
# Purpose : Manage SQLite database operations for answer cache.
# ==========================================================

import os
import sqlite3

DB_NAME = 'database/hr_ai.db'


def create_database():
    os.makedirs(os.path.dirname(DB_NAME), exist_ok=True)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS answer_cache (
            question TEXT PRIMARY KEY,
            answer TEXT
        )
    ''')
    conn.commit()
    conn.close()


def get_cached_answer(question):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT answer FROM answer_cache WHERE question=?', (question,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return None


def save_answer(question, answer):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO answer_cache (question, answer)
        VALUES (?, ?)
    ''', (question, answer))
    conn.commit()
    conn.close()
