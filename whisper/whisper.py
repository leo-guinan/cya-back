import json
import logging
import os

import requests
from decouple import config

from effortless_reach.models import Transcript
from s3.s3_client import S3Client

logger = logging.getLogger(__name__)


class Whisper:
    def __init__(self):
        self.hugging_face_token = config("HUGGING_FACE_TOKEN")
        self.whisper_url = config("WHISPER_URL")

    def transcribe_podcast(self, transcript_id):

        transcript = Transcript.objects.get(id=transcript_id)
        transcript.status = Transcript.TranscriptStatus.PROCESSING
        transcript.save()
        flac_file = transcript.episode.transformed_link
        if not flac_file:
            transcript.status = Transcript.TranscriptStatus.REQUESTED
            transcript.save()
            return
        try:

            logger.info("Downloading podcast from %s", flac_file)
            # download the file
            s3 = S3Client()
            s3.download_file('effortless-reach', f'flac/{transcript.episode.id}/{flac_file}', flac_file)

            files = [('files', open(flac_file, 'rb'))]
            logger.info("Sending podcast to endpoint")
            raw_transcript_response = requests.post(self.whisper_url, files=files)

            # format of response [ {
            #  filename: "file.ext",
            #  transcript: "transcript text"
            # } ]
            logger.info("Parsing response")
            logger.debug(raw_transcript_response.text)
            transcript_response = json.loads(raw_transcript_response.text)
            transcript.text = transcript_response[flac_file]
            transcript.status = Transcript.TranscriptStatus.COMPLETED
            transcript.save()
        except Exception as e:
            transcript.status = Transcript.TranscriptStatus.FAILED
            transcript.error = str(e)
            transcript.save()
            raise e
        finally:
            os.remove(flac_file)
