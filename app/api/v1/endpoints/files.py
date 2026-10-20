from fastapi import APIRouter, Depends, HTTPException
from app.core.s3 import s3_client 
from app.core.logging import logger
import os 
from app.db.crud.deps import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import DocumentCreate, ShareDocumentRequest, SharedDocumentResponse
from app.db.crud.documents import create_document, get_documents_for_user, delete_user_document, share_document_with_user, get_shared_documents_for_user
from app.auth.dependencies import get_current_user
from uuid import UUID
from typing import List


router = APIRouter()

@router.get("/generate_presigned_url")
async def generate_presigned_url(filename: str, expiration : int, content_type : str, current_user = Depends(get_current_user)):
    try:
        s3_key = f"users/{current_user.id}/{filename}"

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
        raise HTTPException(
            status_code=500,
            detail="Failed to generate presigned url"
        )


@router.post("/documents")
async def document(payload: DocumentCreate, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    logger.info(f"Creating document in db")
    document_info = await create_document(payload, db, current_user.id)
    return document_info

@router.get("/get_documents")
async def get_documents(current_user = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    logger.info(f"Getting user documents")
    user_documents = await get_documents_for_user(current_user.id, db)
    return [
        {
            "id": str(doc.id),
            "filename": doc.filename,
            "created_at": doc.created_at,
        }
        for doc in user_documents
    ] 

@router.delete("/documents/{document_id}")
async def delete_document(document_id: str, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    logger.info(f"Deleting document")
    message = await delete_user_document(document_id, db, current_user.id)
    return message

@router.post("/documents/{document_id}/share")
async def share_document(payload: ShareDocumentRequest, document_id: UUID, current_user = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    message = await share_document_with_user(payload, document_id, UUID(current_user.id), db)
    return message

@router.get("/shared_documents", response_model=List[SharedDocumentResponse])
async def get_shared_documents(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_shared_documents_for_user(current_user,db)
