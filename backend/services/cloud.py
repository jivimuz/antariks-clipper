import boto3
from botocore.exceptions import NoCredentialsError
import os
from pathlib import Path

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_S3_BUCKET = os.getenv('AWS_S3_BUCKET')
AWS_S3_REGION = os.getenv('AWS_S3_REGION', 'ap-southeast-1')

def upload_file_to_s3(file_path: Path, s3_key: str) -> str:
    """Upload file to S3 and return the public URL"""
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_S3_REGION
    )
    try:
        s3.upload_file(str(file_path), AWS_S3_BUCKET, s3_key, ExtraArgs={"ACL": "public-read", "ContentType": "video/mp4"})
        url = f"https://{AWS_S3_BUCKET}.s3.{AWS_S3_REGION}.amazonaws.com/{s3_key}"
        return url
    except NoCredentialsError:
        raise RuntimeError("AWS credentials not found")
    except Exception as e:
        raise RuntimeError(f"S3 upload error: {e}")
