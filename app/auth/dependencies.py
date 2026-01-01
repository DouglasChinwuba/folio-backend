from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status
from db.crud.deps import get_db
from firebase_admin import auth
from db.crud.users import get_or_create_user


security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security),db: AsyncSession = Depends(get_db)):
    try:
        
        token = credentials.credentials

        decoded = auth.verify_id_token(token)

        user_info = {
            "google_sub": decoded["uid"],
            "email": decoded.get("email"),
            "name": decoded.get("name"),
        }

        user = await get_or_create_user(db, user_info)

        return user

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
        )