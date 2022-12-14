from marketing.convertkit import Convertkit
from followed.config import CLIENT_NAME


APPS_TO_FORMS = {
    'FOLLOWED': 3859726
}
def add_user_to_app_list(email, app_name):
    try:
        convertkit = Convertkit()
        return convertkit.add_subscriber_to_form(APPS_TO_FORMS[app_name], email)
    except Exception as e:
        print(e)
