import boto3
from dotenv import load_dotenv

load_dotenv()

s3_client = boto3.client("s3")