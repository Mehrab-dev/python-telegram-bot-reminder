from urllib.parse import urlencode
import requests
from app.core.settings import setting 


class GoogleOAuthHandler:
    def __init__(self):
        self.client_id = setting.GOOGLE_CLIENT_ID
        self.client_secret = setting.GOOGLE_SECRET_ID
        self.redirect_uri = setting.REDIRECT_URI
        self.auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        
    def get_auth_link(self, user_id):
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'https://www.googleapis.com/auth/calendar.events',
            'access_type': 'offline',
            'prompt': 'consent',
            'state': str(user_id)
        }
        return f"{self.auth_url}?{urlencode(params)}"
    
    def exchange_code_for_tokens(self, code):
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri
        }
        
        response = requests.post(self.token_url, data=data)
        
        if response.status_code == 200:
            tokens = response.json()
            return {
                'access_token': tokens.get('access_token'),
                'refresh_token': tokens.get('refresh_token'),
                'expires_in': tokens.get('expires_in', 3600)
            }
        else:
            raise Exception(f"Error exchanging code: {response.text}")