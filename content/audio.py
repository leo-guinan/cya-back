import logging
import os

from content.transcriber import Transcriber
logger = logging.getLogger(__name__)

def extract_audio(video):
    # extract audio from video
    pass


def transcribe_audio(audio_file) -> list:
    """Transcribe audio file and return list of chunks"""
    chunks = []
    try:
        transcriber = Transcriber()
        chunks = transcriber.transcribe(audio_file)
    except Exception as e:
        logger.error(e)
    finally:
        os.remove(audio_file)
        return chunks
