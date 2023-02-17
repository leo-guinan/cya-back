import boto3
from decouple import config


class S3Client:
    def __init__(self):
        self.s3 = boto3.client('s3', aws_access_key_id=config('AWS_ACCESS_KEY_ID'),
                               aws_secret_access_key=config('AWS_SECRET_ACCESS_KEY'))

    def download_file(self, bucket, key, file_path):
        self.s3.download_file(bucket, key, file_path)

    def upload_file(self, file_path, bucket, key ):
        self.s3.upload_file(file_path, bucket, key)