import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_path: str = "app_history.db"):
        """Initialize database connection and create tables if they don't exist"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create necessary tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table for storing user actions/history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_type TEXT NOT NULL,
                action_data TEXT,
                timestamp TEXT NOT NULL,
                date TEXT NOT NULL,
                week_number INTEGER,
                year INTEGER
            )
        ''')
        
        # Table for storing app settings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
        
        # Table for storing search history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_query TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                date TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_action(self, action_type: str, action_data: Optional[Dict] = None):
        """Log a user action to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now()
        timestamp = now.isoformat()
        date = now.strftime("%Y-%m-%d")
        week_number = now.isocalendar()[1]
        year = now.year
        
        action_data_str = json.dumps(action_data) if action_data else None
        
        cursor.execute('''
            INSERT INTO user_actions (action_type, action_data, timestamp, date, week_number, year)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (action_type, action_data_str, timestamp, date, week_number, year))
        
        conn.commit()
        conn.close()
    
    def get_recent_actions(self, days: int = 7, limit: int = 50) -> List[Dict]:
        """Get recent actions from the last N days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT action_type, action_data, timestamp, date
            FROM user_actions
            WHERE date >= date('now', '-' || ? || ' days')
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (days, limit))
        
        results = []
        for row in cursor.fetchall():
            action_data = json.loads(row[1]) if row[1] else None
            results.append({
                'action_type': row[0],
                'action_data': action_data,
                'timestamp': row[2],
                'date': row[3]
            })
        
        conn.close()
        return results
    
    def get_actions_by_week(self, week_number: int, year: int) -> List[Dict]:
        """Get actions for a specific week"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT action_type, action_data, timestamp, date
            FROM user_actions
            WHERE week_number = ? AND year = ?
            ORDER BY timestamp DESC
        ''', (week_number, year))
        
        results = []
        for row in cursor.fetchall():
            action_data = json.loads(row[1]) if row[1] else None
            results.append({
                'action_type': row[0],
                'action_data': action_data,
                'timestamp': row[2],
                'date': row[3]
            })
        
        conn.close()
        return results
    
    def save_search(self, query: str):
        """Save a search query to history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now()
        timestamp = now.isoformat()
        date = now.strftime("%Y-%m-%d")
        
        cursor.execute('''
            INSERT INTO search_history (search_query, timestamp, date)
            VALUES (?, ?, ?)
        ''', (query, timestamp, date))
        
        conn.commit()
        conn.close()
    
    def get_search_history(self, limit: int = 20) -> List[str]:
        """Get recent search queries"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT search_query
            FROM search_history
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        results = [row[0] for row in cursor.fetchall()]
        conn.close()
        return results
    
    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a setting value"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT value FROM app_settings WHERE key = ?', (key,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else default
    
    def set_setting(self, key: str, value: str):
        """Set a setting value"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO app_settings (key, value)
            VALUES (?, ?)
        ''', (key, value))
        
        conn.commit()
        conn.close()

