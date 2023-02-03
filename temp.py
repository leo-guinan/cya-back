import requests

files = [('files', open('text.mp3', 'rb'))]
image_embedding_response = requests.post("http://152.70.113.87/transcribe/", files=files)
print(image_embedding_response.text)