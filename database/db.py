import sqlite3
import os
from datetime import datetime
from pathlib import Path

class Database:
    def __init__(self, db_path=None):
        if db_path is None:
            # Place database in the same directory as the project
            self.db_path = str(Path(__file__).resolve().parent.parent / "edu_master.db")
        else:
            self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id INTEGER PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    class_name TEXT NOT NULL,
                    registration_date TEXT NOT NULL,
                    is_blocked INTEGER DEFAULT 0
                )
            """)
            
            # Tests table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tests (
                    code TEXT PRIMARY KEY,
                    subject TEXT NOT NULL,
                    pdf_path TEXT,
                    correct_answers TEXT NOT NULL,
                    duration INTEGER NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1
                )
            """)
            
            # Results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL,
                    test_code TEXT NOT NULL,
                    correct_count INTEGER NOT NULL,
                    wrong_count INTEGER NOT NULL,
                    percentage REAL NOT NULL,
                    submission_time TEXT NOT NULL,
                    duration_spent INTEGER NOT NULL,
                    FOREIGN KEY (telegram_id) REFERENCES users(telegram_id),
                    FOREIGN KEY (test_code) REFERENCES tests(code)
                )
            """)
            
            # Certificates table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS certificates (
                    id TEXT PRIMARY KEY,
                    telegram_id INTEGER NOT NULL,
                    test_code TEXT NOT NULL,
                    issue_date TEXT NOT NULL,
                    pdf_path TEXT,
                    image_path TEXT,
                    FOREIGN KEY (telegram_id) REFERENCES users(telegram_id),
                    FOREIGN KEY (test_code) REFERENCES tests(code)
                )
            """)
            
            # Admins table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    telegram_id INTEGER PRIMARY KEY,
                    added_date TEXT NOT NULL
                )
            """)
            
            # Channels table for mandatory subscription
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS channels (
                    channel_id TEXT PRIMARY KEY,
                    url TEXT NOT NULL
                )
            """)

            # Migration: Add is_gift to tests if not exists
            try:
                cursor.execute("ALTER TABLE tests ADD COLUMN is_gift INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass  # Already exists
                
            conn.commit()

    # User operations
    def get_user(self, telegram_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def add_user(self, telegram_id, full_name, phone, class_name):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            reg_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT OR REPLACE INTO users (telegram_id, full_name, phone, class_name, registration_date, is_blocked)
                VALUES (?, ?, ?, ?, ?, 0)
            """, (telegram_id, full_name, phone, class_name, reg_date))
            conn.commit()

    def update_user(self, telegram_id, **kwargs):
        if not kwargs:
            return
        fields = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [telegram_id]
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE users SET {fields} WHERE telegram_id = ?", tuple(values))
            conn.commit()

    def get_all_users(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            return [dict(row) for row in cursor.fetchall()]

    def count_users(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            return cursor.fetchone()[0]

    # Admin operations
    def is_admin(self, telegram_id, default_admin_id=None):
        if default_admin_id and telegram_id == default_admin_id:
            return True
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM admins WHERE telegram_id = ?", (telegram_id,))
            return cursor.fetchone() is not None

    def add_admin(self, telegram_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            added_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT OR IGNORE INTO admins (telegram_id, added_date)
                VALUES (?, ?)
            """, (telegram_id, added_date))
            conn.commit()

    def remove_admin(self, telegram_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM admins WHERE telegram_id = ?", (telegram_id,))
            conn.commit()

    def get_all_admins(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM admins")
            return [dict(row) for row in cursor.fetchall()]

    # Channels operations
    def add_channel(self, channel_id, url):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO channels (channel_id, url)
                VALUES (?, ?)
            """, (channel_id, url))
            conn.commit()

    def remove_channel(self, channel_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
            conn.commit()

    def get_all_channels(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM channels")
            return [dict(row) for row in cursor.fetchall()]

    # Test operations
    def get_test(self, code):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tests WHERE code = ?", (code,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def add_test(self, code, subject, pdf_path, correct_answers, duration, start_time, end_time, is_gift=0):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO tests (code, subject, pdf_path, correct_answers, duration, start_time, end_time, is_active, is_gift)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
            """, (code, subject, pdf_path, correct_answers, duration, start_time, end_time, is_gift))
            conn.commit()

    def get_gift_tests(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tests WHERE is_gift = 1 ORDER BY code")
            return [dict(row) for row in cursor.fetchall()]

    def delete_test(self, code):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tests WHERE code = ?", (code,))
            cursor.execute("DELETE FROM results WHERE test_code = ?", (code,))
            cursor.execute("DELETE FROM certificates WHERE test_code = ?", (code,))
            conn.commit()

    def get_all_tests(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tests ORDER BY code")
            return [dict(row) for row in cursor.fetchall()]

    def update_test_status(self, code, is_active):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE tests SET is_active = ? WHERE code = ?", (is_active, code))
            conn.commit()

    def update_test(self, code, **kwargs):
        if not kwargs:
            return
        fields = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [code]
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE tests SET {fields} WHERE code = ?", tuple(values))
            conn.commit()

    # Result operations
    def add_result(self, telegram_id, test_code, correct_count, wrong_count, percentage, duration_spent):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            sub_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO results (telegram_id, test_code, correct_count, wrong_count, percentage, submission_time, duration_spent)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (telegram_id, test_code, correct_count, wrong_count, percentage, sub_time, duration_spent))
            conn.commit()
            return cursor.lastrowid

    def get_user_results(self, telegram_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.*, t.subject 
                FROM results r 
                JOIN tests t ON r.test_code = t.code 
                WHERE r.telegram_id = ? 
                ORDER BY r.submission_time DESC
            """, (telegram_id,))
            return [dict(row) for row in cursor.fetchall()]

    def has_participated(self, telegram_id, test_code):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM results WHERE telegram_id = ? AND test_code = ?", (telegram_id, test_code))
            return cursor.fetchone() is not None

    def get_test_results(self, test_code):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.*, u.full_name, u.phone, u.class_name 
                FROM results r 
                JOIN users u ON r.telegram_id = u.telegram_id 
                WHERE r.test_code = ? 
                ORDER BY r.percentage DESC, r.duration_spent ASC
            """, (test_code,))
            return [dict(row) for row in cursor.fetchall()]

    def get_user_rank(self, telegram_id, test_code):
        results = self.get_test_results(test_code)
        for rank, res in enumerate(results, 1):
            if res["telegram_id"] == telegram_id:
                return rank, len(results)
        return None, len(results)

    def get_test_leaderboard(self, test_code, limit=10):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.percentage, u.full_name, u.class_name
                FROM results r
                JOIN users u ON r.telegram_id = u.telegram_id
                WHERE r.test_code = ?
                ORDER BY r.percentage DESC, r.duration_spent ASC
                LIMIT ?
            """, (test_code, limit))
            return [dict(row) for row in cursor.fetchall()]

    # Statistics operations
    def get_statistics(self):
        stats = {}
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Total users
            cursor.execute("SELECT COUNT(*) FROM users")
            stats["total_users"] = cursor.fetchone()[0]
            
            # Active users (users who worked at least one test)
            cursor.execute("SELECT COUNT(DISTINCT telegram_id) FROM results")
            stats["active_users"] = cursor.fetchone()[0]
            
            # Total participants (total results)
            cursor.execute("SELECT COUNT(*) FROM results")
            stats["total_results"] = cursor.fetchone()[0]
            
            # Scores stats
            cursor.execute("SELECT MAX(percentage), MIN(percentage), AVG(percentage) FROM results")
            row = cursor.fetchone()
            if row and row[0] is not None:
                stats["highest_score"] = round(row[0], 1)
                stats["lowest_score"] = round(row[1], 1)
                stats["average_score"] = round(row[2], 1)
            else:
                stats["highest_score"] = 0
                stats["lowest_score"] = 0
                stats["average_score"] = 0
                
            # Certificates count
            cursor.execute("SELECT COUNT(*) FROM certificates")
            stats["certificates_count"] = cursor.fetchone()[0]
            
        return stats

    # Certificate operations
    def add_certificate(self, cert_id, telegram_id, test_code, pdf_path, image_path):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            issue_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT OR REPLACE INTO certificates (id, telegram_id, test_code, issue_date, pdf_path, image_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (cert_id, telegram_id, test_code, issue_date, pdf_path, image_path))
            conn.commit()

    def get_certificate(self, cert_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM certificates WHERE id = ?", (cert_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_user_certificates(self, telegram_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.*, t.subject, r.percentage, r.correct_count
                FROM certificates c
                JOIN tests t ON c.test_code = t.code
                JOIN results r ON c.telegram_id = r.telegram_id AND c.test_code = r.test_code
                WHERE c.telegram_id = ?
                ORDER BY c.issue_date DESC
            """, (telegram_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_global_leaderboard(self, limit=10):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.full_name, u.class_name, 
                       COUNT(r.id) as tests_count, 
                       ROUND(AVG(r.percentage), 1) as avg_score
                FROM users u
                JOIN results r ON u.telegram_id = r.telegram_id
                GROUP BY u.telegram_id
                ORDER BY avg_score DESC, tests_count DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_user_global_rank(self, telegram_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT telegram_id, ROUND(AVG(percentage), 1) as avg_score, COUNT(id) as tests_count
                FROM results
                GROUP BY telegram_id
                ORDER BY avg_score DESC, tests_count DESC
            """)
            rows = cursor.fetchall()
            for rank, row in enumerate(rows, 1):
                if row["telegram_id"] == telegram_id:
                    return rank, len(rows)
            return None, len(rows)
