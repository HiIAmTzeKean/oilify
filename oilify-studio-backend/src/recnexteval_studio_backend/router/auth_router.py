import logging as logger
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from recnexteval_studio_backend.config.setting import get_settings
from recnexteval_studio_backend.db.connection import get_db
from recnexteval_studio_backend.db.schema import StreamUser
from recnexteval_studio_backend.services.auth import (
    create_access_token,
    decode_token,
    get_current_username,
    verify_password,
)

logger = logger.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def create_auth_router() -> APIRouter:
    router = APIRouter(prefix="/auth", tags=["auth"])

    @router.post("/token")
    async def login_for_access_token(
        db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
    ):
        user = db.query(StreamUser).filter(StreamUser.username == form_data.username).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )
        if not verify_password(plain_password=form_data.password, hashed_password=user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )

        access_token_expires = timedelta(minutes=get_settings().ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            user_id=user.id,
            username=user.username,
            expires_delta=access_token_expires,
        )
        return {"access_token": access_token, "token_type": "bearer"}

    @router.get("/me")
    async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
        try:
            payload = decode_token(token)
            return {"user_id": payload.get("user_id"), "username": payload.get("username")}
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    @router.get("/users")
    def list_users(
        db: Session = Depends(get_db), current_username: str = Depends(get_current_username)
    ) -> list[dict]:
        """Return all users (id and username). Protected endpoint."""
        users = db.query(StreamUser).all()
        return [{"id": u.id, "username": u.username} for u in users]

    return router
