from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import User

async def get_or_create_user(db: AsyncSession, user_info: dict) -> str:
    google_sub = user_info["google_sub"]
    email = user_info["email"]
    name = user_info.get("name")

    stmt = select(User).where(User.google_sub == google_sub)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        return str(user.id)

    user = User(
        google_sub=google_sub,
        email=email,
        name=name,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return str(user.id)