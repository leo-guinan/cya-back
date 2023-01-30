import json

import requests
from decouple import config

from effortless_reach.models import Transcript


class Whisper:
    def __init__(self):
        self.hugging_face_token = config("HUGGING_FACE_TOKEN")
        self.whisper_url = config("WHISPER_URL")
    def transcribe_podcast(self, transcript_id):

        transcript = Transcript.objects.get(id=transcript_id)
        transcript.status = Transcript.TranscriptStatus.PROCESSING
        transcript.save()
        url = transcript.episode.download_link
        try:

            r = requests.get(url)
            data = r.content


            headers = {
                'Authorization': f'Bearer {self.hugging_face_token}',
                'Content-Type': 'audio/mpeg',
            }


            response = requests.post(self.whisper_url, headers=headers, data=data)
            transcribed_text = json.loads(response.content.decode("utf-8"))

            transcript.text = transcribed_text['text']
            transcript.status = Transcript.TranscriptStatus.COMPLETED
            transcript.save()
        except Exception as e:
            transcript.status = Transcript.TranscriptStatus.FAILED
            transcript.error = str(e)
            transcript.save()
            raise e

