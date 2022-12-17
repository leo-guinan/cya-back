from mail.service import send_email
from podcast_toolkit.models import Podcast


def send_podcast_components(podcast_id):
    podcast = Podcast.objects.filter(id=podcast_id).first()
    if podcast is not None:
        message = f'{podcast.show_notes}'
        send_email(
            to=podcast.request.from_email,
            message=message,
            subject=f"Show Notes for {podcast.title}",
        )