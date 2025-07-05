import logging
from datetime import datetime
from modules.utils.user_analytics import user_stats

def generate_daily_report():
    report = f"Daily Report - {datetime.now().strftime('%Y-%m-%d')}\n"
    for user_id, stats in user_stats.items():
        report += f"User {user_id}: {stats}\n"
    logging.info(report)
    # Extend to email or Telegram message sending here
