from sqlalchemy import Column, String, TIMESTAMP, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from .session import Base
from pydantic import BaseModel, EmailStr
from uuid import UUID as PyUUID



class User(Base):
    __tablename__ = "users"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    google_sub = Column(String(64), unique=True, nullable=False)
    email = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    documents = relationship(
        "Document",
        back_populates="owner",
        cascade="all, delete-orphan"
    )


class Document(Base):
    __tablename__ = "documents"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(Text, nullable=False)
    s3_key = Column(Text, nullable=False)
    owner_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="documents")


class DocumentShare(Base):
    __tablename__ = "document_shares"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    document_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False
    )

    share_token = Column(String, unique=True, index=True, nullable=False)

    shared_with_email = Column(String, nullable=False)

    expires_at = Column(DateTime, nullable=False)

    created_at = Column(DateTime, server_default=func.now())


class DocumentCreate(BaseModel):
    filename: str
    s3_key: str
    content_type: str

class ShareDocumentRequest(BaseModel):
    email: EmailStr

class SharedDocumentResponse(BaseModel):
    id: PyUUID
    filename: str
    s3_key: str
    owner_id: PyUUID