import sqlite3
import hashlib
from datetime import datetime

class DBManager:
    def __init__(self, db_name='chat_database.db'):
        self.db_name = db_name
        self.init_database()

    def init_database(self):
        """Initialize database with required tables"""
        # Create tables if not exist
        import os
        print(f"[DB] Initializing database at {os.path.abspath(self.db_name)}")
        conn = sqlite3.connect(self.db_name, check_same_thread=False)
        cursor = conn.cursor()
        
        # Users table for authentication
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        
        # Messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                receiver TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, username, password):
        """Register a new user"""
        try:
            print(f"[DB] Attempting to register user: '{username}'")
            conn = sqlite3.connect(self.db_name, check_same_thread=False)
            cursor = conn.cursor()
            
            # Check if username exists
            cursor.execute('SELECT username FROM users WHERE username = ?', (username,))
            if cursor.fetchone():
                print(f"[DB] Username '{username}' already exists")
                conn.close()
                return False, "Username already exists"
            
            # Create new user
            password_hash = self.hash_password(password)
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                'INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)',
                (username, password_hash, created_at)
            )
            conn.commit()
            print(f"[DB] User '{username}' registered successfully")
            conn.close()
            return True, "Registration successful"
        except Exception as e:
            print(f"[DB] Registration error: {e}")
            return False, "Registration failed"

    def authenticate_user(self, username, password):
        """Authenticate a user"""
        try:
            print(f"[DB] Authenticating user: '{username}'")
            conn = sqlite3.connect(self.db_name, check_same_thread=False)
            cursor = conn.cursor()
            
            password_hash = self.hash_password(password)
            cursor.execute(
                'SELECT username FROM users WHERE username = ? AND password_hash = ?',
                (username, password_hash)
            )
            user = cursor.fetchone()
            conn.close()
            
            if user:
                print(f"[DB] User '{username}' logged in successfully")
                return True, "Login successful"
            else:
                print(f"[DB] Login failed for '{username}' (invalid credentials)")
                return False, "Invalid username or password"
        except Exception as e:
            print(f"[DB] Authentication error: {e}")
            return False, "Authentication failed"

    def save_message(self, sender, receiver, message, timestamp):
        """Save message to database"""
        try:
            conn = sqlite3.connect(self.db_name, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO messages (sender, receiver, message, timestamp) VALUES (?, ?, ?, ?)',
                (sender, receiver, message, timestamp)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Database save error: {e}")

    def get_previous_messages(self, username):
        """Retrieve previous messages for a user"""
        try:
            conn = sqlite3.connect(self.db_name, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute(
                'SELECT sender, receiver, message, timestamp FROM messages WHERE receiver = ? OR sender = ? OR receiver = "ALL" ORDER BY id',
                (username, username)
            )
            messages = cursor.fetchall()
            conn.close()
            return messages
        except Exception as e:
            print(f"Database retrieve error: {e}")
            return []
