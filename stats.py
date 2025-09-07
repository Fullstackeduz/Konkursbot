import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List
import os

from database import db
from config import EXCEL_MAX_ROWS

class StatsManager:
    def __init__(self):
        self.db = db

    def get_daily_stats(self, days_ago: int = 0) -> Dict:
        """Get statistics for a specific day"""
        target_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        query = '''
            SELECT new_users, active_users, messages_sent, referrals_made
            FROM bot_statistics 
            WHERE date = ?
        '''
        result = self.db.execute_query(query, (target_date,))
        
        if result:
            return {
                'new_users': result[0][0] or 0,
                'active_users': result[0][1] or 0,
                'messages_sent': result[0][2] or 0,
                'referrals_made': result[0][3] or 0,
                'date': target_date
            }
        else:
            return {
                'new_users': 0,
                'active_users': 0,
                'messages_sent': 0,
                'referrals_made': 0,
                'date': target_date
            }

    def get_weekly_stats(self) -> Dict:
        """Get statistics for the current week"""
        return self.db.get_stats_by_period(7)

    def get_monthly_stats(self) -> Dict:
        """Get statistics for the current month"""
        return self.db.get_stats_by_period(30)

    def get_all_time_stats(self) -> Dict:
        """Get all-time statistics"""
        total_users = self.db.get_total_users()
        active_today = self.db.get_active_users_count(1)
        active_week = self.db.get_active_users_count(7)
        active_month = self.db.get_active_users_count(30)
        
        # Get total referrals
        query = 'SELECT COUNT(*) FROM referrals'
        total_referrals = self.db.execute_query(query)[0][0] or 0
        
        # Get total messages (estimation)
        query = 'SELECT SUM(messages_sent) FROM bot_statistics'
        result = self.db.execute_query(query)
        total_messages = result[0][0] if result and result[0][0] else 0
        
        return {
            'total_users': total_users,
            'active_today': active_today,
            'active_week': active_week,
            'active_month': active_month,
            'total_referrals': total_referrals,
            'total_messages': total_messages
        }

    def get_growth_dynamics(self, days: int = 30) -> List[Dict]:
        """Get user growth dynamics for specified period"""
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        query = '''
            SELECT date, new_users, active_users
            FROM bot_statistics 
            WHERE date >= ?
            ORDER BY date ASC
        '''
        results = self.db.execute_query(query, (start_date,))
        
        dynamics = []
        cumulative_users = 0
        
        for row in results:
            cumulative_users += row[1] or 0
            dynamics.append({
                'date': row[0],
                'new_users': row[1] or 0,
                'active_users': row[2] or 0,
                'cumulative_users': cumulative_users
            })
        
        return dynamics

    def get_top_referrers(self, limit: int = 10) -> List[Dict]:
        """Get top referrers with their statistics"""
        return self.db.get_top_referrers(limit)

    def get_user_activity_stats(self) -> Dict:
        """Get user activity statistics"""
        # Users registered today
        today = datetime.now().strftime('%Y-%m-%d')
        query_today = '''
            SELECT COUNT(*) FROM users 
            WHERE DATE(registration_date) = ?
        '''
        today_registrations = self.db.execute_query(query_today, (today,))[0][0] or 0
        
        # Users registered this week
        week_start = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        query_week = '''
            SELECT COUNT(*) FROM users 
            WHERE DATE(registration_date) >= ?
        '''
        week_registrations = self.db.execute_query(query_week, (week_start,))[0][0] or 0
        
        # Users registered this month
        month_start = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        query_month = '''
            SELECT COUNT(*) FROM users 
            WHERE DATE(registration_date) >= ?
        '''
        month_registrations = self.db.execute_query(query_month, (month_start,))[0][0] or 0
        
        return {
            'today_registrations': today_registrations,
            'week_registrations': week_registrations,
            'month_registrations': month_registrations,
            'active_today': self.db.get_active_users_count(1),
            'active_week': self.db.get_active_users_count(7),
            'active_month': self.db.get_active_users_count(30)
        }

    async def export_users_to_excel(self, limit: int = None) -> str:
        """Export users data to Excel file"""
        if limit is None:
            limit = EXCEL_MAX_ROWS
        
        # Get users data
        users_data = self.db.get_users_for_export(limit)
        
        if not users_data:
            raise ValueError("No users data to export")
        
        # Create DataFrame
        df = pd.DataFrame(users_data)
        
        # Rename columns to Uzbek
        column_mapping = {
            'rank': '№',
            'user_id': 'Foydalanuvchi ID',
            'username': 'Username',
            'first_name': 'Ism',
            'last_name': 'Familiya',
            'phone_number': 'Telefon raqam',
            'balance': 'Ball',
            'registration_date': 'Ro\'yxatdan o\'tgan sana',
            'last_activity': 'Oxirgi faollik',
            'referral_count': 'Referal soni',
            'referrer_name': 'Taklif qiluvchi'
        }
        df = df.rename(columns=column_mapping)
        
        # Format dates
        df['Ro\'yxatdan o\'tgan sana'] = pd.to_datetime(df['Ro\'yxatdan o\'tgan sana']).dt.strftime('%d.%m.%Y %H:%M')
        df['Oxirgi faollik'] = pd.to_datetime(df['Oxirgi faollik']).dt.strftime('%d.%m.%Y %H:%M')
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'users_export_{timestamp}.xlsx'
        filepath = os.path.join('exports', filename)
        
        # Create exports directory if it doesn't exist
        os.makedirs('exports', exist_ok=True)
        
        # Create Excel file with formatting
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Foydalanuvchilar', index=False)
            
            # Get workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Foydalanuvchilar']
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_name = column[0].column_letter
                
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                adjusted_width = min(max_length + 2, 50)  # Max width 50
                worksheet.column_dimensions[column_name].width = adjusted_width
        
        return filepath

    async def export_statistics_to_excel(self) -> str:
        """Export statistics to Excel file"""
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'statistics_export_{timestamp}.xlsx'
        filepath = os.path.join('exports', filename)
        
        # Create exports directory if it doesn't exist
        os.makedirs('exports', exist_ok=True)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            
            # Daily statistics for last 30 days
            daily_stats = []
            for i in range(30):
                day_stats = self.get_daily_stats(i)
                daily_stats.append(day_stats)
            
            daily_df = pd.DataFrame(daily_stats)
            daily_df = daily_df.rename(columns={
                'date': 'Sana',
                'new_users': 'Yangi foydalanuvchilar',
                'active_users': 'Faol foydalanuvchilar',
                'messages_sent': 'Yuborilgan xabarlar',
                'referrals_made': 'Referrallar'
            })
            daily_df.to_excel(writer, sheet_name='Kunlik statistika', index=False)
            
            # Top referrers
            top_referrers = self.get_top_referrers(50)
            if top_referrers:
                referrers_df = pd.DataFrame(top_referrers)
                referrers_df = referrers_df.rename(columns={
                    'user_id': 'Foydalanuvchi ID',
                    'first_name': 'Ism',
                    'last_name': 'Familiya',
                    'username': 'Username',
                    'referral_count': 'Referal soni'
                })
                referrers_df.to_excel(writer, sheet_name='Top referrallar', index=False)
            
            # All-time statistics
            all_time = self.get_all_time_stats()
            stats_data = {
                'Parametr': [
                    'Jami foydalanuvchilar',
                    'Bugun faol',
                    'Hafta davomida faol',
                    'Oy davomida faol',
                    'Jami referrallar',
                    'Jami xabarlar'
                ],
                'Qiymat': [
                    all_time['total_users'],
                    all_time['active_today'],
                    all_time['active_week'],
                    all_time['active_month'],
                    all_time['total_referrals'],
                    all_time['total_messages']
                ]
            }
            stats_df = pd.DataFrame(stats_data)
            stats_df.to_excel(writer, sheet_name='Umumiy statistika', index=False)
            
            # Top users by balance
            top_users = self.db.get_top_users(100)
            if top_users:
                users_df = pd.DataFrame(top_users)
                users_df = users_df.rename(columns={
                    'rank': '№',
                    'user_id': 'Foydalanuvchi ID',
                    'first_name': 'Ism',
                    'last_name': 'Familiya',
                    'username': 'Username',
                    'balance': 'Ball'
                })
                users_df.to_excel(writer, sheet_name='Top foydalanuvchilar', index=False)
        
        return filepath

    def get_contest_statistics(self) -> Dict:
        """Get contest-specific statistics"""
        top_users = self.db.get_top_users(20)
        total_participants = self.db.get_total_users()
        
        # Calculate total points distributed
        query = 'SELECT SUM(balance) FROM users WHERE balance > 0'
        result = self.db.execute_query(query)
        total_points = result[0][0] if result and result[0][0] else 0
        
        # Get average points
        avg_points = total_points / total_participants if total_participants > 0 else 0
        
        return {
            'total_participants': total_participants,
            'total_points_distributed': total_points,
            'average_points': round(avg_points, 2),
            'top_20_users': top_users,
            'contest_active': self.is_contest_active()
        }

    def is_contest_active(self) -> bool:
        """Check if contest is currently active"""
        contest_status = self.db.get_setting('contest_active', 'false')
        return contest_status.lower() == 'true'

    def update_activity_stats(self):
        """Update daily activity statistics"""
        # Count active users today
        active_today = self.db.get_active_users_count(1)
        
        # Count new users today
        today = datetime.now().strftime('%Y-%m-%d')
        query = '''
            SELECT COUNT(*) FROM users 
            WHERE DATE(registration_date) = ?
        '''
        new_today = self.db.execute_query(query, (today,))[0][0] or 0
        
        # Update statistics
        self.db.update_daily_stats(
            new_users=new_today,
            active_users=active_today
        )

# Global stats manager instance
stats_manager = StatsManager()