import logging
import time

import requests
from decouple import config

logger = logging.getLogger(__name__)


class Transcriber:
    def __init__(self):
        self.gladia_key = config('GLADIA_API_KEY')
        self.assemblyai_key = config('ASSEMBLYAI_API_KEY')

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
            parsed = response.json()
            prediction = parsed['prediction']
            chunks = []
            for item in prediction:
                chunks.append(item['transcription'])
            return chunks
        except Exception as e:
            logger.error(e)
            logger.error("Gladia failed. Trying AssemblyAI")
            return self._use_assemblyai(audio_file)

    def _use_assemblyai(self, audio_file):
        logger.info("Using AssemblyAI")
        try:
            upload_path = self._upload_file_to_assembly_ai(audio_file)
            endpoint = "https://api.assemblyai.com/v2/transcript"
            json = {
                "audio_url": upload_path,
                "speaker_labels": True
            }
            headers = {
                "authorization": self.assemblyai_key,
            }
            response = requests.post(endpoint, json=json, headers=headers)
            response.raise_for_status()
            transcript_id = response.json()["id"]
            while True:
                status_endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
                status_response = requests.get(status_endpoint, headers=headers)
                status_response.raise_for_status()
                result = status_response.json()
                status = result["status"]
                if status == "error":

                    raise Exception(result["error"])
                if status == "completed":
                    logger.info("AssemblyAI completed")
                    prediction = result['utterances']
                    chunks = []
                    for item in prediction:
                        chunks.append(item['text'])
                    return chunks
                # wait 10 seconds before checking again
                time.sleep(10)

        except Exception as e:

            logger.error(e)
            return []

    def _upload_file_to_assembly_ai(self, audio_file):
        logger.info("Uploading file to AssemblyAI")
        def read_file(filename, chunk_size=5242880):
            with open(filename, 'rb') as _file:
                while True:
                    data = _file.read(chunk_size)
                    if not data:
                        break
                    yield data

        headers = {'authorization': self.assemblyai_key}
        response = requests.post('https://api.assemblyai.com/v2/upload',
                                 headers=headers,
                                 data=read_file(audio_file))
        response.raise_for_status()
        logger.info("File uploaded to AssemblyAI")
        return response.json()['upload_url']
