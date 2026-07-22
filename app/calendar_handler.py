from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.core.settings import setting


class CalendarHandler:
    def __init__(self, access_token, refresh_token=None):
        self.credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=setting.GOOGLE_CLIENT_ID,
            client_secret=setting.GOOGLE_SECRET_ID
        )
        self.service = build('calendar', 'v3', credentials=self.credentials)
        print("✅ CalendarHandler مقداردهی شد")

    
    def create_event(self, calendar_id, summary, description, start_time, end_time, reminder_minutes=120):
        print(f"📝 در حال ساخت Event: {summary}")
        print(f"📅 Start: {start_time}, End: {end_time}")
        
        event = {
            'summary': summary,
            'description': description or "",
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'Asia/Tehran',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'Asia/Tehran',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 4320},   # ۳ روز قبل (۷۲ ساعت)
                    {'method': 'popup', 'minutes': 1440},   # ۱ روز قبل (۲۴ ساعت)
                    {'method': 'popup', 'minutes': 120},    # ۲ ساعت قبل
                ],
            },
        }
        
        print(f"📦 Event Body: {event}")
        
        try:
            print("🚀 ارسال به Google API...")
            event = self.service.events().insert(calendarId=calendar_id, body=event).execute()
            print(f"✅ Event ساخته شد: {event.get('id')}")
            return event.get('id')
        except HttpError as error:
            print(f"❌ خطای HttpError: {error}")
            print(f"❌ جزئیات: {error.content}")
            raise Exception(f"Error creating event: {error}")
        except Exception as e:
            print(f"❌ خطای عمومی: {e}")
            import traceback
            traceback.print_exc()
            raise

    def create_calendar(self, name):
        """ساخت تقویم جدید برای کاربر"""
        calendar = {
            'summary': name,
            'timeZone': 'Asia/Tehran'
        }
        created_calendar = self.service.calendars().insert(body=calendar).execute()
        return created_calendar.get('id')