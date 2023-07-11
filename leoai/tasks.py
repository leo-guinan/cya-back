from backend.celery import app
from leoai.notion import Notion
from leoai.youtube import process_video


@app.task(name="leoai.transcribe_youtube_video")
def transcribe_youtube_video(video_url, page):
    chunks = process_video(video_url)
    notion = Notion()
    notion.add_chunks_to_page(page, chunks)
