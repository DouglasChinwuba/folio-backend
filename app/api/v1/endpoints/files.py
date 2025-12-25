from fastapi import APIRouter, Depends
import boto3
import logging
import os 
from pydantic import BaseModel
from db.crud.deps import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from db.crud.documents import load_document

router = APIRouter()
s3_client = boto3.client('s3')

logger = logging.getLogger()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

class DocumentCreate(BaseModel):
    filename: str
    s3_key: str
    content_type: str
    owner_id: str

@router.get("/generate_presigned_url")
async def generate_presigned_url(user_id: str, filename: str, expiration : int, content_type : str):
    try:
        s3_key = f"users/{user_id}/{filename}"

        presigned_url = s3_client.generate_presigned_url("put_object", 
                Params={
                    "Bucket": os.getenv("BUCKET_NAME"),
                    "Key": s3_key,
                    "ContentType": content_type 
                },
            ExpiresIn=expiration,
            HttpMethod='PUT'
        )
        logger.info(f"Created presigned url: {presigned_url}")
        return {
            "presigned_url": presigned_url,
            "s3_key": s3_key,
        }

    except Exception as e:
        logger.error("Error creating presigned url")


@router.post("/documents")
async def document(payload: DocumentCreate, db: AsyncSession = Depends(get_db)):
    document_info = await load_document(payload, db)
    return document_info
