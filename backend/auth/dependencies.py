from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from backend.database.db import get_db
from backend.database.models import User
from backend.auth.security import decode_access_token


def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token.")

    token = authorization.split(" ")[1]
    user_id = decode_access_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")
    return user