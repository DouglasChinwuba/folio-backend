from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Document
from pydantic import BaseModel
from sqlalchemy import select
from uuid import UUID


class DocumentCreate(BaseModel):
    filename: str
    s3_key: str
    content_type: str

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
