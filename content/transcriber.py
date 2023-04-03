import logging

import requests
from decouple import config
logger = logging.getLogger(__name__)


class Transcriber:
    def __init__(self):
        self.gladia_key = config('GLADIA_API_KEY')

    def transcribe(self, audio_file):
        return self._use_gladia(audio_file)

    def _use_gladia(self, audio_file):
        url = "https://api.gladia.io/audio/text/audio-transcription/?model=large-v2"

        files = {"audio": (audio_file, open(audio_file, "rb"), "audio/mpeg")}
        payload = {
            "language_behaviour": "automatic single language",
            "toggle_noise_reduction": "false",
            "toggle_diarization": "false",
            "toggle_direct_translate": "false",
            "toggle_text_emotion_recognition": "false",
            "toggle_summarization": "false",
            "toggle_chapterization": "false",
            "diarization_max_speakers": "2",
            "output_format": "json"
        }
        headers = {
            "accept": "application/json",
            'x-gladia-key': self.gladia_key,

        }

        response = requests.post(url, data=payload, files=files, headers=headers)
        try:
            prediction = response.json()['prediction']
            chunks = []
            for item in prediction:
                chunks.append(item['transcription'])
            return chunks
        except Exception as e:
            print(e)
            return []



    def _use_assemblyai(self, audio_file):
        pass