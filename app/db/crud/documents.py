from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Document
from pydantic import BaseModel
import os


class DocumentCreate(BaseModel):
    filename: str
    s3_key: str
    content_type: str
    owner_id: str

async def load_document(payload: DocumentCreate, db: AsyncSession) -> str:
    bucket_name = os.getenv("BUCKET_NAME")

    doc = Document(
        filename=payload.filename,
        s3_key=payload.s3_key,
        owner_id=payload.owner_id
    )

    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    return {
        "id": str(doc.id),
        "filename": doc.filename,
        "s3_key": doc.s3_key
    }