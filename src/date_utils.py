from datetime import datetime, timedelta

class DateUtils:
    @staticmethod
    def get_current_week_dates():
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        return [monday + timedelta(days=i) for i in range(7)]

    @staticmethod
    def get_week_dates(weeks_ago):
        today = datetime.now()
        monday = today - timedelta(days=today.weekday() + (7 * weeks_ago))
        return [monday + timedelta(days=i) for i in range(7)]

    @staticmethod
    def get_date_for_day(week_dates, day_of_week):
        days = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3,
                'Friday': 4, 'Saturday': 5, 'Sunday': 6}
        return week_dates[days[day_of_week]].strftime('%Y-%m-%d')

    @staticmethod
    def get_today_day_of_week():
        return datetime.now().strftime('%A')

    @staticmethod
    def format_week_label(weeks_ago):
        today = datetime.now()
        monday = today - timedelta(days=today.weekday() + (7 * weeks_ago))
        if weeks_ago == 0:
            return f"Current Week ({monday.strftime('%Y-%m-%d')})"
        return f"{weeks_ago} Weeks Ago ({monday.strftime('%Y-%m-%d')})"
