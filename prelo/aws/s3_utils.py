import tempfile

import boto3
import markdown
import pdfkit
from botocore.exceptions import ClientError
from decouple import config


def create_presigned_url(bucket_name, object_name, expiration=3600, method='PUT'):
    """
    Generate a presigned URL to share an S3 object
    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :param method: HTTP method (e.g., 'GET' for downloading, 'PUT' for uploading)
    :return: Presigned URL as string. If error, returns None.
    """
    s3_client = boto3.client('s3',
                             aws_access_key_id=config('PRELO_AWS_ACCESS_KEY_ID'),
                             aws_secret_access_key=config('PRELO_AWS_SECRET_ACCESS_KEY'),
                             region_name=config('PRELO_AWS_REGION')
                             )

    try:
        if method == 'GET':
            response = s3_client.generate_presigned_url('get_object',
                                                        Params={'Bucket': bucket_name,
                                                                'Key': object_name},
                                                        ExpiresIn=expiration)
        elif method == 'PUT':
            response = s3_client.generate_presigned_url('put_object',
                                                        Params={
                                                            'Bucket': bucket_name,
                                                            'Key': object_name,
                                                            'ContentType': 'application/pdf'
                                                        },
                                                        ExpiresIn=expiration,
                                                        HttpMethod=method)
    except Exception as e:
        print(f"Error generating presigned URL: {e}")
        return None

    return response


def file_exists(key):
    """
    Check if a file exists in an S3 bucket at a specific key.

    :param bucket: str, the name of the bucket
    :param key: str, the key path in the bucket
    :return: bool, True if the file exists, False otherwise
    """
    s3 = boto3.client('s3',
                      aws_access_key_id=config('PRELO_AWS_ACCESS_KEY_ID'),
                      aws_secret_access_key=config('PRELO_AWS_SECRET_ACCESS_KEY'),
                      region_name=config('PRELO_AWS_REGION')
                      )
    try:
        bucket = config('PRELO_AWS_BUCKET')
        # Attempt to retrieve the metadata of the specified object
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        # If a client error is thrown, check if it was a 404 error
        # which means the object does not exist.
        if e.response['Error']['Code'] == '404':
            return False
        else:
            # Rethrow the exception if it wasn't a 404 error
            raise


def download_file_from_s3(key):
    """
    Download a file from S3 to a specified path on the local server.

    :param bucket: str, the S3 bucket name
    :param key: str, the S3 key for the file
    :param download_path: str, the local path to download the file
    """
    bucket = config('PRELO_AWS_BUCKET')
    s3 = boto3.client('s3',
                      aws_access_key_id=config('PRELO_AWS_ACCESS_KEY_ID'),
                      aws_secret_access_key=config('PRELO_AWS_SECRET_ACCESS_KEY'),
                      region_name=config('PRELO_AWS_REGION')
                      )
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file_path = temp_file.name

    # Download the file from S3 into the temporary file
    s3.download_file(Bucket=bucket, Key=key, Filename=temp_file_path)

    # Close the file handle
    temp_file.close()

    return temp_file_path


def upload_file_to_s3(key, input_file):
    bucket = config('PRELO_AWS_BUCKET')
    s3 = boto3.client('s3',
                      aws_access_key_id=config('PRELO_AWS_ACCESS_KEY_ID'),
                      aws_secret_access_key=config('PRELO_AWS_SECRET_ACCESS_KEY'),
                      region_name=config('PRELO_AWS_REGION')
                      )
    s3.upload_file(Filename=input_file, Bucket=bucket, Key=key)

def upload_uploaded_file_to_s3(key, uploaded_file):
    bucket = config('PRELO_AWS_BUCKET')
    s3 = boto3.client('s3',
                      aws_access_key_id=config('PRELO_AWS_ACCESS_KEY_ID'),
                      aws_secret_access_key=config('PRELO_AWS_SECRET_ACCESS_KEY'),
                      region_name=config('PRELO_AWS_REGION')
                      )
    s3.upload_fileobj(
        uploaded_file,
        config('PRELO_AWS_BUCKET'),
        key,
        ExtraArgs={'ContentType': uploaded_file.content_type},

    )


def markdown_to_pdf(markdown_content, output_path):
    """
    Convert Markdown content to a PDF file.

    :param markdown_content: str, the Markdown content to convert
    :param output_path: str, the path to save the PDF file
    """
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')

    # Convert markdown to HTML
    html_content = markdown.markdown(markdown_content)

    # Generate PDF from HTML
    pdfkit.from_string(html_content, temp_pdf.name)

    # Save the HTML content to a temporary file

    upload_file_to_s3(output_path, temp_pdf.name)


def html_to_pdf(html_content, output_path):
    """
    Convert Markdown content to a PDF file.

    :param html_content: str, the html content to convert
    :param output_path: str, the path to save the PDF file
    """
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')

    # Generate PDF from HTML
    pdfkit.from_string(html_content, temp_pdf.name, options={"enable-local-file-access": True}, verbose=True)

    # Save the HTML content to a temporary file

    upload_file_to_s3(output_path, temp_pdf.name)