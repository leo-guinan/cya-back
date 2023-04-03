from os.path import splitext

import requests
from decouple import config


class Converter:
    def __init__(self, path):
        self.base_url = config('CONVERT_BASE_URL')
        self.flac_path=self.base_url + 'convert/audio/to/flac'
        self.extract_audio_path=self.base_url + 'convert/video/extract/audio'


    def convert_video_to_audio(self, path):
        converted_filename = "%s.flac" % splitext(path)[0]
        files = [('files', open(path, 'rb'))]
        response = requests.post(self.extract_audio_path, files=files)
        open(converted_filename, 'wb').write(response.content)
        return converted_filename