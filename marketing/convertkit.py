import requests
from decouple import config


class Convertkit:
    BASE_URL = 'https://api.convertkit.com/v3/'
    def __init__(self):
        self.api_key = config('CONVERTKIT_API_KEY')

    def add_subscriber_to_form(self, form_id, email):
        url = f"{self.BASE_URL}forms/{form_id}/subscribe"
        data = {
            "api_key": self.api_key,
            "email": email
        }
        response = requests.post(url, data=data)
        return response.json()
