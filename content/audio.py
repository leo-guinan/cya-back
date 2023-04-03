from content.transcriber import Transcriber


def extract_audio(video):
    # extract audio from video
    pass


def transcribe_audio(audio_file) -> list:
    """Transcribe audio file and return list of chunks"""
    transcriber = Transcriber()
    return transcriber.transcribe(audio_file)
