from fastapi import APIRouter, Depends
import boto3
import logging
import os 
from pydantic import BaseModel
from db.crud.deps import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from db.crud.documents import create_document, get_documents_for_user
from auth.dependencies import get_current_user

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

@router.get("/generate_presigned_url")
async def generate_presigned_url(filename: str, expiration : int, content_type : str, current_user_id = Depends(get_current_user)):
    try:
        s3_key = f"users/{current_user_id}/{filename}"

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
async def document(payload: DocumentCreate, db: AsyncSession = Depends(get_db), current_user_id = Depends(get_current_user)):
    document_info = await create_document(payload, db, current_user_id)
    return document_info

@router.get("/get_documents")
async def get_documents(current_user_id = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user_documents = await get_documents_for_user(current_user_id, db)
    return [
        {
            "id": str(doc.id),
            "filename": doc.filename,
            "created_at": doc.created_at,
        }
        for doc in user_documents
    ] 