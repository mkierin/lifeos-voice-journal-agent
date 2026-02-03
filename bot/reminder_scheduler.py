import logging
from datetime import datetime, timedelta
from dateutil import parser as dateparser
from dateutil.relativedelta import relativedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot
from .vector_store import VectorStore
from .config import TELEGRAM_TOKEN

logger = logging.getLogger(__name__)

class ReminderScheduler:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.vector_store = VectorStore()
        self.scheduler = AsyncIOScheduler()

    def start(self):
        """Start the reminder scheduler"""
        # Check for due reminders every day at 9 AM
        self.scheduler.add_job(
            self.check_and_send_reminders,
            'cron',
            hour=9,
            minute=0,
            id='daily_reminder_check'
        )
        self.scheduler.start()
        logger.info("Reminder scheduler started - checking daily at 9 AM")

    async def check_and_send_reminders(self):
        """Check for due reminders and send notifications"""
        logger.info("Checking for due reminders...")

        # Get all open tasks (including reminders)
        try:
            all_tasks = self.vector_store.get_all_tasks(status="open")

            now = datetime.now()
            for task in all_tasks:
                payload = task.payload
                due_date_str = payload.get('due_date')

                if not due_date_str:
                    continue

                try:
                    due_date = datetime.fromisoformat(due_date_str)

                    # If reminder is due (date has passed or is today)
                    if due_date.date() <= now.date():
                        user_id = payload.get('user_id')
                        description = payload.get('description', '')

                        # Send notification to user
                        message = f"⏰ Reminder: {description}"

                        try:
                            await self.bot.send_message(
                                chat_id=user_id,
                                text=message
                            )
                            logger.info(f"Sent reminder to user {user_id}: {description}")
                        except Exception as e:
                            logger.error(f"Failed to send reminder to user {user_id}: {e}")

                except Exception as e:
                    logger.error(f"Error processing reminder: {e}")

        except Exception as e:
            logger.error(f"Error checking reminders: {e}")

    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Reminder scheduler stopped")


def parse_natural_date(date_string: str) -> datetime:
    """
    Parse natural language dates like 'Tuesday', 'next week', 'in 3 days'
    Returns a datetime object
    """
    date_string = date_string.lower().strip()
    now = datetime.now()

    # Handle "tomorrow"
    if date_string == "tomorrow":
        return now + timedelta(days=1)

    # Handle "today"
    if date_string == "today":
        return now

    # Handle day names (monday, tuesday, etc.)
    days_of_week = {
        'monday': 0, 'mon': 0,
        'tuesday': 1, 'tue': 1, 'tues': 1,
        'wednesday': 2, 'wed': 2,
        'thursday': 3, 'thu': 3, 'thur': 3, 'thurs': 3,
        'friday': 4, 'fri': 4,
        'saturday': 5, 'sat': 5,
        'sunday': 6, 'sun': 6
    }

    for day_name, day_num in days_of_week.items():
        if day_name in date_string:
            current_day = now.weekday()
            days_ahead = day_num - current_day

            # If the day is today or has passed this week, schedule for next week
            if days_ahead <= 0:
                days_ahead += 7

            # If "next" is mentioned, add another week
            if "next" in date_string:
                days_ahead += 7

            return now + timedelta(days=days_ahead)

    # Handle "next week"
    if "next week" in date_string:
        return now + timedelta(weeks=1)

    # Handle "next month"
    if "next month" in date_string:
        return now + relativedelta(months=1)

    # Handle "in X days/weeks/months"
    if "in" in date_string:
        parts = date_string.split()
        try:
            idx = parts.index("in")
            if idx + 2 < len(parts):
                num = int(parts[idx + 1])
                unit = parts[idx + 2].lower()

                if "day" in unit:
                    return now + timedelta(days=num)
                elif "week" in unit:
                    return now + timedelta(weeks=num)
                elif "month" in unit:
                    return now + relativedelta(months=num)
                elif "hour" in unit:
                    return now + timedelta(hours=num)
        except (ValueError, IndexError):
            pass

    # Try using dateutil parser as fallback
    try:
        return dateparser.parse(date_string, fuzzy=True)
    except:
        # Default to tomorrow if parsing fails
        return now + timedelta(days=1)


def calculate_days_until(target_date: datetime) -> int:
    """Calculate number of days from now until target date"""
    now = datetime.now()
    delta = target_date - now
    return max(0, delta.days)
