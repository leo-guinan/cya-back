import json
import logging

import requests
from decouple import config

import os
from os.path import splitext
from pydub import AudioSegment



def wav_to_flac(wav_path, flac_path):
    song = AudioSegment.from_wav(wav_path)
    song.export(flac_path, format="flac")
    return flac_path


def mp3_to_flac(mp3_path, flac_path):
    song = AudioSegment.from_mp3(mp3_path)
    song.export(flac_path, format="flac")
    return flac_path


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
        file_name = url.split("/")[-1]
        file_name = file_name.split("?")[0]
        converted_filename = "%s.flac" % splitext(file_name)[0]
        try:

            logger.info("Downloading podcast from %s", url)
            # download the file
            r = requests.get(url)
            # get the file name

            with open(file_name, "wb") as f:
                f.write(r.content)
            # convert to flac
            converted_file = ""
            logger.info("Converting podcast to flac")
            if file_name.endswith(".mp3"):
                converted_file = mp3_to_flac(file_name, converted_filename)
            elif file_name.endswith(".wav"):
                converted_file = wav_to_flac(file_name, converted_filename)

            files = [('files', open(converted_file, 'rb'))]
            logger.info("Sending podcast to endpoint")
            raw_transcript_response = requests.post(self.whisper_url, files=files)

            # format of response [ {
            #  filename: "file.ext",
            #  transcript: "transcript text"
            # } ]
            logger.info("Parsing response")
            logger.debug(raw_transcript_response.text)
            transcript_response = json.loads(raw_transcript_response.text)
            transcript.text = transcript_response[converted_file]
            transcript.status = Transcript.TranscriptStatus.COMPLETED
            transcript.save()
        except Exception as e:
            transcript.status = Transcript.TranscriptStatus.FAILED
            transcript.error = str(e)
            transcript.save()
            raise e
        finally:
            os.remove(file_name)
            os.remove(converted_filename)


