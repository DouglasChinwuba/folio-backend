from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Document, DocumentCreate, ShareDocumentRequest, DocumentShare
from sqlalchemy import select
from uuid import UUID
from app.core.s3 import s3_client 
import os 
from fastapi import HTTPException
import secrets
from datetime import datetime, timedelta
import resend
from app.core.logging import logger

resend.api_key = os.getenv("RESEND_API_KEY")

async def create_document(payload: DocumentCreate, db: AsyncSession, current_user_id):

    doc = Document(
        filename=payload.filename,
        s3_key=payload.s3_key,
        owner_id=current_user_id
    )

    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    return {
        "id": str(doc.id),
        "filename": doc.filename,
        "s3_key": doc.s3_key
    }

async def get_documents_for_user(owner_id: UUID, db: AsyncSession):
    stmt = (
        select(Document)
        .where(Document.owner_id == owner_id)
        .order_by(Document.created_at.desc())
    )

    result = await db.execute(stmt)
    return result.scalars().all()

async def delete_user_document(document_id: str, db: AsyncSession, current_user_id):
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.owner_id == current_user_id
        )
    )

    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        s3_client.delete_object(
            Bucket=os.getenv("BUCKET_NAME"),
            Key=doc.s3_key
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete file from S3"
        )
    
    await db.delete(doc)
    await db.commit()

    return {"message": "Document deleted successfully"}

async def share_document_with_user(payload: ShareDocumentRequest, document_id: UUID, current_user_id, db: AsyncSession):
    doc = await db.get(Document, document_id)

    logger.info(f"doc.owner_id: {type(doc.owner_id)}")

    logger.info(f"current_user_id: {type(current_user_id)}")

    if not doc or doc.owner_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    share_token = secrets.token_urlsafe(32)

    share = DocumentShare(
        document_id=document_id,
        shared_with_email=payload.email,
        share_token=share_token,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )

    db.add(share)
    await db.commit()

    share_link = f"{os.getenv('API_BASE_URL')}/shared?token={share_token}"
    send_share_email(payload.email, share_link, doc.filename)

    return {"message": "Document shared successfully"}

def send_share_email(
    to_email: str,
    share_link: str,
    filename: str
):
    resend.Emails.send({
        "from":"onboarding@resend.dev", 
        "to":to_email,
        "subject":f"{filename} was shared with you",
        "html":f"""
        <div style="font-family: Arial, sans-serif">
            <h2>File Shared</h2>
            <p><strong>{filename}</strong> was shared with you.</p>
            <p>
                <a href="{share_link}"
                   style="
                     background:#2563eb;
                     color:white;
                     padding:10px 16px;
                     text-decoration:none;
                     border-radius:6px;
                   ">
                   View file
                </a>
            </p>
            <p>This link will expire in 7 days.</p>
        </div>
        """
    })

async def get_shared_documents_for_user(current_user, db: AsyncSession):
    query = (
        select(Document)
        .join(DocumentShare, Document.id == DocumentShare.document_id)
        .where(DocumentShare.shared_with_email == current_user.email)
    )
    result = await db.execute(query)
    shared_docs = result.scalars().all()
    
    return shared_docs