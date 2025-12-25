from fastapi import APIRouter, Depends
from pydantic import BaseModel
import os 
import firebase_admin
from firebase_admin import auth, credentials
from sqlalchemy.ext.asyncio import AsyncSession
from db.crud.deps import get_db
from db.crud.users import get_or_create_user 


router = APIRouter()

cred = credentials.Certificate(os.getenv("FIREBASE_KEY_PATH"))
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

class GoogleLoginPayload(BaseModel):
    id_token: str

def verify_google_token(token: str):
    decoded_token = auth.verify_id_token(token)
    return {
        "google_sub": decoded_token["uid"],  
        "email": decoded_token.get("email"),
        "name": decoded_token.get("name")
    }

@router.post("/auth/google")
async def google_login(payload: GoogleLoginPayload, db: AsyncSession = Depends(get_db)):
    # Verify token with Google / Firebase
    user_info = verify_google_token(payload.id_token)

    # Upsert user in DB
    user_id = await get_or_create_user(db, user_info)

    return {
        "user_id": str(user_id),
        "email": user_info["email"],
        "name": user_info["name"]
    }

