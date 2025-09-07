import sqlite3
import asyncio
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import threading

class Database:
    def __init__(self, db_path: str = 'bot_database.db'):
        self.db_path = db_path
        self.lock = threading.Lock()
        self.init_db()

    def init_db(self):
        """Initialize database with all required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    phone_number TEXT,
                    balance INTEGER DEFAULT 0,
                    referrer_id INTEGER,
                    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Admins table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admins (
                    user_id INTEGER PRIMARY KEY,
                    added_by INTEGER,
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    permissions TEXT DEFAULT 'full'
                )
            ''')
            
            # Mandatory subscriptions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mandatory_subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id TEXT NOT NULL,
                    channel_username TEXT,
                    channel_title TEXT,
                    channel_type TEXT DEFAULT 'channel',
                    is_private BOOLEAN DEFAULT FALSE,
                    invite_link TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # User subscriptions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_subscriptions (
                    user_id INTEGER,
                    channel_id TEXT,
                    subscription_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_joined BOOLEAN DEFAULT TRUE,
                    PRIMARY KEY (user_id, channel_id)
                )
            ''')
            
            # Referrals table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS referrals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER,
                    referred_id INTEGER,
                    bonus_given INTEGER DEFAULT 0,
                    referral_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (referrer_id) REFERENCES users (user_id),
                    FOREIGN KEY (referred_id) REFERENCES users (user_id)
                )
            ''')
            
            # Contest settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contest_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Messages log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS message_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    message_type TEXT,
                    message_text TEXT,
                    sent_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN DEFAULT TRUE
                )
            ''')
            
            # Bot statistics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bot_statistics (
                    date TEXT PRIMARY KEY,
                    new_users INTEGER DEFAULT 0,
                    active_users INTEGER DEFAULT 0,
                    messages_sent INTEGER DEFAULT 0,
                    referrals_made INTEGER DEFAULT 0
                )
            ''')
            
            conn.commit()

    def execute_query(self, query: str, params: tuple = ()) -> List[tuple]:
        """Execute a query and return results"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return cursor.fetchall()

    def execute_insert(self, query: str, params: tuple = ()) -> int:
        """Execute insert query and return lastrowid"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.lastrowid

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute update query and return affected rows"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount

    # User methods
    def add_user(self, user_id: int, username: str = None, first_name: str = None, 
                last_name: str = None, phone_number: str = None, referrer_id: int = None) -> bool:
        """Add new user to database"""
        try:
            query = '''
                INSERT OR IGNORE INTO users 
                (user_id, username, first_name, last_name, phone_number, referrer_id, balance)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            '''
            params = (user_id, username, first_name, last_name, phone_number, referrer_id, 2)
            return self.execute_insert(query, params) > 0
        except:
            return False

    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        query = '''
            SELECT user_id, username, first_name, last_name, phone_number, 
                   balance, referrer_id, registration_date, is_active, last_activity
            FROM users WHERE user_id = ?
        '''
        result = self.execute_query(query, (user_id,))
        if result:
            columns = ['user_id', 'username', 'first_name', 'last_name', 'phone_number', 
                      'balance', 'referrer_id', 'registration_date', 'is_active', 'last_activity']
            return dict(zip(columns, result[0]))
        return None

    def update_user_phone(self, user_id: int, phone_number: str) -> bool:
        """Update user phone number"""
        query = 'UPDATE users SET phone_number = ?, last_activity = CURRENT_TIMESTAMP WHERE user_id = ?'
        return self.execute_update(query, (phone_number, user_id)) > 0

    def add_balance(self, user_id: int, amount: int) -> bool:
        """Add balance to user"""
        query = 'UPDATE users SET balance = balance + ?, last_activity = CURRENT_TIMESTAMP WHERE user_id = ?'
        return self.execute_update(query, (amount, user_id)) > 0

    def get_user_balance(self, user_id: int) -> int:
        """Get user balance"""
        query = 'SELECT balance FROM users WHERE user_id = ?'
        result = self.execute_query(query, (user_id,))
        return result[0][0] if result else 0

    def get_user_rank(self, user_id: int) -> int:
        """Get user rank by balance"""
        query = '''
            SELECT COUNT(*) + 1 FROM users 
            WHERE balance > (SELECT balance FROM users WHERE user_id = ?) AND is_active = TRUE
        '''
        result = self.execute_query(query, (user_id,))
        return result[0][0] if result else 0

    def get_top_users(self, limit: int = 20) -> List[Dict]:
        """Get top users by balance"""
        query = '''
            SELECT user_id, first_name, last_name, username, balance,
                   ROW_NUMBER() OVER (ORDER BY balance DESC, registration_date ASC) as rank
            FROM users WHERE is_active = TRUE AND balance > 0
            ORDER BY balance DESC, registration_date ASC
            LIMIT ?
        '''
        results = self.execute_query(query, (limit,))
        users = []
        for row in results:
            users.append({
                'user_id': row[0],
                'first_name': row[1],
                'last_name': row[2],
                'username': row[3],
                'balance': row[4],
                'rank': row[5]
            })
        return users

    # Admin methods
    def add_admin(self, user_id: int, added_by: int = None) -> bool:
        """Add admin"""
        query = 'INSERT OR IGNORE INTO admins (user_id, added_by) VALUES (?, ?)'
        return self.execute_insert(query, (user_id, added_by)) > 0

    def remove_admin(self, user_id: int) -> bool:
        """Remove admin"""
        query = 'DELETE FROM admins WHERE user_id = ?'
        return self.execute_update(query, (user_id,)) > 0

    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        query = 'SELECT 1 FROM admins WHERE user_id = ?'
        return len(self.execute_query(query, (user_id,))) > 0

    def get_admins(self) -> List[Dict]:
        """Get all admins"""
        query = '''
            SELECT a.user_id, u.first_name, u.last_name, u.username, a.added_date
            FROM admins a
            LEFT JOIN users u ON a.user_id = u.user_id
            ORDER BY a.added_date ASC
        '''
        results = self.execute_query(query)
        admins = []
        for row in results:
            admins.append({
                'user_id': row[0],
                'first_name': row[1],
                'last_name': row[2],
                'username': row[3],
                'added_date': row[4]
            })
        return admins

    # Subscription methods
    def add_mandatory_subscription(self, channel_id: str, channel_username: str = None, 
                                 channel_title: str = None, channel_type: str = 'channel',
                                 is_private: bool = False, invite_link: str = None) -> bool:
        """Add mandatory subscription"""
        query = '''
            INSERT OR REPLACE INTO mandatory_subscriptions 
            (channel_id, channel_username, channel_title, channel_type, is_private, invite_link)
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        params = (channel_id, channel_username, channel_title, channel_type, is_private, invite_link)
        return self.execute_insert(query, params) > 0

    def get_mandatory_subscriptions(self) -> List[Dict]:
        """Get all mandatory subscriptions"""
        query = '''
            SELECT id, channel_id, channel_username, channel_title, channel_type, 
                   is_private, invite_link, is_active
            FROM mandatory_subscriptions WHERE is_active = TRUE
        '''
        results = self.execute_query(query)
        subscriptions = []
        for row in results:
            subscriptions.append({
                'id': row[0],
                'channel_id': row[1],
                'channel_username': row[2],
                'channel_title': row[3],
                'channel_type': row[4],
                'is_private': row[5],
                'invite_link': row[6],
                'is_active': row[7]
            })
        return subscriptions

    def remove_mandatory_subscription(self, subscription_id: int) -> bool:
        """Remove mandatory subscription"""
        query = 'UPDATE mandatory_subscriptions SET is_active = FALSE WHERE id = ?'
        return self.execute_update(query, (subscription_id,)) > 0

    # Referral methods
    def add_referral(self, referrer_id: int, referred_id: int) -> bool:
        """Add referral"""
        query = 'INSERT OR IGNORE INTO referrals (referrer_id, referred_id, bonus_given) VALUES (?, ?, ?)'
        from config import REFERRAL_BONUS
        success = self.execute_insert(query, (referrer_id, referred_id, REFERRAL_BONUS)) > 0
        if success:
            # Add bonus to referrer
            self.add_balance(referrer_id, REFERRAL_BONUS)
        return success

    def get_referral_count(self, user_id: int) -> int:
        """Get referral count for user"""
        query = 'SELECT COUNT(*) FROM referrals WHERE referrer_id = ?'
        result = self.execute_query(query, (user_id,))
        return result[0][0] if result else 0

    def get_top_referrers(self, limit: int = 10) -> List[Dict]:
        """Get top referrers"""
        query = '''
            SELECT r.referrer_id, u.first_name, u.last_name, u.username, COUNT(*) as referral_count
            FROM referrals r
            LEFT JOIN users u ON r.referrer_id = u.user_id
            GROUP BY r.referrer_id
            ORDER BY referral_count DESC
            LIMIT ?
        '''
        results = self.execute_query(query, (limit,))
        referrers = []
        for row in results:
            referrers.append({
                'user_id': row[0],
                'first_name': row[1],
                'last_name': row[2],
                'username': row[3],
                'referral_count': row[4]
            })
        return referrers

    # Contest settings methods
    def set_setting(self, key: str, value: str) -> bool:
        """Set contest setting"""
        query = '''
            INSERT OR REPLACE INTO contest_settings (key, value, updated_date) 
            VALUES (?, ?, CURRENT_TIMESTAMP)
        '''
        return self.execute_insert(query, (key, value)) >= 0

    def get_setting(self, key: str, default: str = None) -> str:
        """Get contest setting"""
        query = 'SELECT value FROM contest_settings WHERE key = ?'
        result = self.execute_query(query, (key,))
        return result[0][0] if result else default

    # Statistics methods
    def update_daily_stats(self, new_users: int = 0, active_users: int = 0, 
                          messages_sent: int = 0, referrals_made: int = 0):
        """Update daily statistics"""
        today = datetime.now().strftime('%Y-%m-%d')
        query = '''
            INSERT OR REPLACE INTO bot_statistics 
            (date, new_users, active_users, messages_sent, referrals_made)
            VALUES (?, 
                    COALESCE((SELECT new_users FROM bot_statistics WHERE date = ?), 0) + ?,
                    ?,
                    COALESCE((SELECT messages_sent FROM bot_statistics WHERE date = ?), 0) + ?,
                    COALESCE((SELECT referrals_made FROM bot_statistics WHERE date = ?), 0) + ?)
        '''
        self.execute_insert(query, (today, today, new_users, active_users, today, messages_sent, today, referrals_made))

    def get_stats_by_period(self, days: int) -> Dict:
        """Get statistics for specified period"""
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        query = '''
            SELECT 
                COALESCE(SUM(new_users), 0) as total_new_users,
                COALESCE(SUM(messages_sent), 0) as total_messages,
                COALESCE(SUM(referrals_made), 0) as total_referrals,
                COALESCE(AVG(active_users), 0) as avg_active_users
            FROM bot_statistics 
            WHERE date >= ?
        '''
        result = self.execute_query(query, (start_date,))
        if result:
            return {
                'new_users': int(result[0][0]),
                'messages_sent': int(result[0][1]),
                'referrals_made': int(result[0][2]),
                'avg_active_users': int(result[0][3])
            }
        return {'new_users': 0, 'messages_sent': 0, 'referrals_made': 0, 'avg_active_users': 0}

    def get_total_users(self) -> int:
        """Get total registered users"""
        query = 'SELECT COUNT(*) FROM users WHERE phone_number IS NOT NULL'
        result = self.execute_query(query)
        return result[0][0] if result else 0

    def get_active_users_count(self, days: int = 1) -> int:
        """Get active users in last N days"""
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        query = 'SELECT COUNT(*) FROM users WHERE last_activity >= ?'
        result = self.execute_query(query, (cutoff_date,))
        return result[0][0] if result else 0

    def search_user(self, search_term: str) -> List[Dict]:
        """Search users by ID, username, or name"""
        # Try to search by user ID first if it's a number
        try:
            user_id = int(search_term)
            user = self.get_user(user_id)
            if user:
                return [user]
        except ValueError:
            pass
        
        # Search by username or name
        search_pattern = f'%{search_term}%'
        query = '''
            SELECT user_id, username, first_name, last_name, phone_number, balance, registration_date
            FROM users 
            WHERE username LIKE ? OR first_name LIKE ? OR last_name LIKE ?
            ORDER BY balance DESC
            LIMIT 20
        '''
        results = self.execute_query(query, (search_pattern, search_pattern, search_pattern))
        users = []
        for row in results:
            users.append({
                'user_id': row[0],
                'username': row[1],
                'first_name': row[2],
                'last_name': row[3],
                'phone_number': row[4],
                'balance': row[5],
                'registration_date': row[6]
            })
        return users

    def reset_all_balances(self) -> bool:
        """Reset all user balances to 0"""
        query = 'UPDATE users SET balance = 0'
        return self.execute_update(query) >= 0

    def get_users_for_export(self, limit: int = None) -> List[Dict]:
        """Get users data for Excel export"""
        query = '''
            SELECT u.user_id, u.username, u.first_name, u.last_name, u.phone_number, 
                   u.balance, u.registration_date, u.last_activity,
                   COALESCE(r.referral_count, 0) as referral_count,
                   COALESCE(ur.referrer_name, '') as referrer_name
            FROM users u
            LEFT JOIN (
                SELECT referrer_id, COUNT(*) as referral_count
                FROM referrals GROUP BY referrer_id
            ) r ON u.user_id = r.referrer_id
            LEFT JOIN (
                SELECT referred_id, 
                       COALESCE(ru.first_name || ' ' || ru.last_name, ru.username, CAST(ru.user_id AS TEXT)) as referrer_name
                FROM referrals ref
                LEFT JOIN users ru ON ref.referrer_id = ru.user_id
            ) ur ON u.user_id = ur.referred_id
            WHERE u.phone_number IS NOT NULL
            ORDER BY u.balance DESC, u.registration_date ASC
        '''
        if limit:
            query += f' LIMIT {limit}'
            
        results = self.execute_query(query)
        users = []
        for i, row in enumerate(results, 1):
            users.append({
                'rank': i,
                'user_id': row[0],
                'username': row[1],
                'first_name': row[2],
                'last_name': row[3],
                'phone_number': row[4],
                'balance': row[5],
                'registration_date': row[6],
                'last_activity': row[7],
                'referral_count': row[8],
                'referrer_name': row[9]
            })
        return users

# Global database instance
db = Database()