from mail.service import send_email
from podcast_toolkit.models import Podcast


def send_podcast_components(podcast_id):
    podcast = Podcast.objects.filter(id=podcast_id).first()
    if podcast is not None:
        message= f'''
        Show Notes:
        {podcast.show_notes}
        
        Summary:
        {podcast.summary}
        
        Key Points:
        {podcast.key_points}
        
        Links to Include:
        {podcast.links_to_include}
        '''
        send_email(
            to=podcast.request.from_email,
            message=message,
            subject="Podcast Components",


        )