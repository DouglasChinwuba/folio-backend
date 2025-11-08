from fastapi import APIRouter
import boto3
import logging
import os 
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()
s3_client = boto3.client('s3')

logger = logging.getLogger()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)


@router.get("/generate_presigned_url")
async def generate_presigned_url(object_name, expiration, content_type):
    try:
        url = s3_client.generate_presigned_url("put_object", 
                Params={
                    "Bucket": os.getenv("BUCKET_NAME"),
                    "Key": object_name,
                    "ContentType": content_type 
                },
            ExpiresIn=expiration,
            HttpMethod='PUT'
        )
        logger.info(f"Created presigned url: {url}")
        return url
    except Exception as e:
        logger.error("Error creating presigned url")
