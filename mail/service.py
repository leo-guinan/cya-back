from decouple import config
from python_http_client import HTTPError
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import *

FROM_EMAIL = 'leo@definet.dev'


# def send_email(to, message, client=None):
#     message = Mail(
#         from_email=FROM_EMAIL,
#         to_emails=To(email=to, dynamic_template_data={
#             "tweets": [
#                 {
#                     "twitterProfileImgURL": "https://pbs.twimg.com/profile_images/1547929810046840836/AQDnpT0a_normal.png",
#                     "authorName": "Leo Guinan",
#                     "authorUsername": "leo_guinan",
#                     "message": "This is a fake tweet"
#                 },
#                 {
#                     "twitterProfileImgURL": "https://pbs.twimg.com/profile_images/1547929810046840836/AQDnpT0a_normal.png",
#                     "authorName": "Leo Guinan",
#                     "authorUsername": "leo_guinan",
#                     "message": "This is another fake tweet"
#                 }
#             ]
#
#         }),
#         subject='Testing template',
#     )
#     message.template_id = 'd-e723d5a50a8b493c918a8516bae6fc94'
#     try:
#         sg = SendGridAPIClient(config('SENDGRID_API_KEY'))
#         response = sg.send(message)
#         code, body, headers = response.status_code, response.body, response.headers
#         print(f"Response Code: {code} ")
#         print(f"Response Body: {body} ")
#         print(f"Response Headers: {headers} ")
#         print("Message Sent!")
#         return str(response.status_code)
#     except HTTPError as e:
#         print("Error: {0}".format(e.to_dict))
#         return str("error")
#     # sg = sendgrid.SendGridAPIClient(api_key=config('SENDGRID_API_KEY'))
#     # from_email = Email("leo@definet.dev")
#     # to_email = To("leo.guinan@gmail.com")
#     # subject = "Sending with SendGrid is Fun"
#     # content = Content("text/plain", "and easy to do anywhere, even with Python")
#     # mail = Mail(from_email, to_email, subject, content)
#     # response = sg.client.mail.send.post(request_body=mail.get())
#     # print(response.status_code)
#     # print(response.body)
#     # print(response.headers)

def send_email(to, message, subject, client=None):
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=To(email=to),
        subject=subject,
        plain_text_content=message
    )
    try:
        sg = SendGridAPIClient(config('SENDGRID_API_KEY'))
        response = sg.send(message)
        return str(response.status_code)
    except HTTPError as e:
        print("Error: {0}".format(e.to_dict))
        return str("error")
