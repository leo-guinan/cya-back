import json
import logging

import requests
from decouple import config
import hashlib

from effortless_reach.models import Transcript
import boto3
logger = logging.getLogger(__name__)

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

            logger.info("Downloading podcast from %s", url)
            r = requests.get(url)
            data = r.content
            # upload to s3
            s3 = boto3.client('s3')
            owner_email = transcript.episode.podcast.rss_feed.owner.email
            podcast_name = transcript.episode.podcast.title
            owner_podcast_hash = hashlib.md5(f'{owner_email}-{podcast_name}'.lower().encode()).hexdigest()
            s3.put_object(Body=data, Bucket='effortless-reach', Key=f'incoming/{owner_podcast_hash}/{transcript_id}.mp3')
            transcript.hash = owner_podcast_hash
            transcript.save()
        except Exception as e:
            transcript.status = Transcript.TranscriptStatus.FAILED
            transcript.error = str(e)
            transcript.save()
            raise e

