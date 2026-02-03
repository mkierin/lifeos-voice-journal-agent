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
        # Check for due reminders every 15 minutes
        self.scheduler.add_job(
            self.check_and_send_reminders,
            'interval',
            minutes=15,
            id='reminder_check'
        )
        self.scheduler.start()
        logger.info("Reminder scheduler started - checking every 15 minutes")

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

                    # If reminder is due (current time has passed the due time)
                    if due_date <= now:
                        user_id = payload.get('user_id')
                        description = payload.get('description', '')
                        task_id = task.id

                        # Send notification to user
                        message = f"⏰ Reminder: {description}"

                        try:
                            await self.bot.send_message(
                                chat_id=user_id,
                                text=message
                            )
                            logger.info(f"Sent reminder to user {user_id}: {description}")

                            # Mark reminder as completed after sending
                            self.vector_store.upsert_task(
                                user_id=user_id,
                                task_id=task_id,
                                description=description,
                                status="completed"
                            )
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
    Parse natural language dates and times like:
    - 'today at 3pm', 'tomorrow at 12', 'Tuesday at 18:30'
    - 'in 2 hours', 'in 30 minutes'
    - 'next week', 'in 3 days'
    Returns a datetime object
    """
    import re

    date_string = date_string.lower().strip()
    now = datetime.now()

    # Extract time component if present (e.g., "at 3pm", "at 15:30", "at 12")
    time_match = re.search(r'at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', date_string)
    target_time = None

    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2)) if time_match.group(2) else 0
        am_pm = time_match.group(3)

        # Handle AM/PM
        if am_pm == 'pm' and hour < 12:
            hour += 12
        elif am_pm == 'am' and hour == 12:
            hour = 0

        target_time = (hour, minute)
        # Remove time part from string for date parsing
        date_string = re.sub(r'at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?', '', date_string).strip()

    # Handle "in X minutes/hours"
    if "in" in date_string:
        parts = date_string.split()
        try:
            idx = parts.index("in")
            if idx + 2 <= len(parts):
                num = int(parts[idx + 1])
                unit = parts[idx + 2].lower() if idx + 2 < len(parts) else ""

                if "minute" in unit:
                    return now + timedelta(minutes=num)
                elif "hour" in unit:
                    return now + timedelta(hours=num)
                elif "day" in unit:
                    result = now + timedelta(days=num)
                    if target_time:
                        result = result.replace(hour=target_time[0], minute=target_time[1], second=0, microsecond=0)
                    return result
                elif "week" in unit:
                    result = now + timedelta(weeks=num)
                    if target_time:
                        result = result.replace(hour=target_time[0], minute=target_time[1], second=0, microsecond=0)
                    return result
        except (ValueError, IndexError):
            pass

    # Handle "tomorrow"
    if "tomorrow" in date_string:
        result = now + timedelta(days=1)
        if target_time:
            result = result.replace(hour=target_time[0], minute=target_time[1], second=0, microsecond=0)
        else:
            result = result.replace(hour=9, minute=0, second=0, microsecond=0)  # Default 9 AM
        return result

    # Handle "today"
    if "today" in date_string or date_string == "":
        result = now
        if target_time:
            result = result.replace(hour=target_time[0], minute=target_time[1], second=0, microsecond=0)
            # If time has already passed today, schedule for tomorrow
            if result <= now:
                result = result + timedelta(days=1)
        return result

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

            result = now + timedelta(days=days_ahead)
            if target_time:
                result = result.replace(hour=target_time[0], minute=target_time[1], second=0, microsecond=0)
            else:
                result = result.replace(hour=9, minute=0, second=0, microsecond=0)  # Default 9 AM
            return result

    # Handle "next week" / "next month"
    if "next week" in date_string:
        result = now + timedelta(weeks=1)
        if target_time:
            result = result.replace(hour=target_time[0], minute=target_time[1], second=0, microsecond=0)
        return result

    if "next month" in date_string:
        result = now + relativedelta(months=1)
        if target_time:
            result = result.replace(hour=target_time[0], minute=target_time[1], second=0, microsecond=0)
        return result

    # Try using dateutil parser as fallback
    try:
        parsed = dateparser.parse(date_string, fuzzy=True)
        if parsed and target_time:
            parsed = parsed.replace(hour=target_time[0], minute=target_time[1], second=0, microsecond=0)
        return parsed if parsed else now + timedelta(hours=1)
    except:
        # Default to 1 hour from now if parsing fails
        return now + timedelta(hours=1)


def calculate_days_until(target_date: datetime) -> int:
    """Calculate number of days from now until target date"""
    now = datetime.now()
    delta = target_date - now
    return max(0, delta.days)
