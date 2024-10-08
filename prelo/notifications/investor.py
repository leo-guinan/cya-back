from django.core.mail import send_mail
from django.conf import settings
from prelo.models import Investor
from django.core.mail import send_mail, get_connection
import json
import os
from decouple import config

def investor_created(investor: Investor):
    with get_connection(
        host=config('LOOPS_SMTP_HOST'),
        port=config('LOOPS_SMTP_PORT'),
        username=config('LOOPS_SMTP_USER'),
        password=config('LOOPS_SMTP_PASSWORD'),
        use_tls=True # Has to be True
    ) as connection:

        # This payload can be copied from a transactional email's 
        #  Publish page in Loops
        payload = {
            "transactionalId": "cm20s6oew00dztsdpxh33xq75",
            "email": investor.email,
            "dataVariables": {
                "name": investor.first_name,                
            }
        }
       
        send_mail(
            "Subject here", # Overwritten by Loops template
            json.dumps(payload), # Stringify the payload
            "from@example.com", # Overwritten by Loops template
            [investor.email],
            fail_silently=False,
            connection=connection
        )

    

