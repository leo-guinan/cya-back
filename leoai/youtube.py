import logging

from pytube import YouTube, Playlist

from content.audio import transcribe_audio

logger = logging.getLogger(__name__)
def download(link):

    try:
        video = YouTube(link)
        audio = video.streams.get_audio_only()
        name = audio.download()
        logger.info("Download is completed successfully")
        return name
    except Exception as e:
        logger.error(f"An error has occurred: {e}")
        return None
def process_video(video_url):
    # ... do something with the url
    #download video
    audio = download(video_url)

    return transcribe_audio(audio)


