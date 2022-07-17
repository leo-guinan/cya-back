from decouple import config
import requests

class TweetPik:
    def __init__(self):
        self.api_key = config('TWEETPIK_API_KEY')
        self.bucket = config('TWEETPIK_BUCKET')

    def create_image(self, tweet_id):
        url = 'https://tweetpik.com/api/images'
        data = {
            'tweetId': tweet_id
        }
        headers = {
            "Authorization": self.api_key
        }
        response = requests.post(url, data=data, headers=headers)

