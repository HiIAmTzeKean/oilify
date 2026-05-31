from datetime import timedelta

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from recnexteval_studio_backend.config.setting import get_settings
from recnexteval_studio_backend.db.connection import get_db
from recnexteval_studio_backend.db.schema import StreamUser
from recnexteval_studio_backend.services.auth import create_access_token, hash_password

# Configure OAuth
oauth = OAuth()
oauth.register(
    name="google",
    client_id=get_settings().GOOGLE_CLIENT_ID,
    client_secret=get_settings().GOOGLE_CLIENT_SECRET,
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    authorize_params={"scope": "openid email profile"},
    access_token_url="https://oauth2.googleapis.com/token",
    client_kwargs={"scope": "openid email profile"},
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
)


def create_auth_google_router() -> APIRouter:
    router = APIRouter(prefix="/auth/google", tags=["auth"])

    @router.get("/")
    async def auth_google(request: Request) -> RedirectResponse:
        return await oauth.google.authorize_redirect(request, redirect_uri="http://localhost:9000/api/v1/auth/google/callback")

    @router.get("/callback")
    async def google_callback(request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
        try:
            token = await oauth.google.authorize_access_token(request)
            user_info = token.get("userinfo") or {}

            # Extract user details
            email = user_info.get("email")
            if not email:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email not provided by Google")

            # Check if user exists
            user = db.query(StreamUser).filter(StreamUser.email == email).first()
            if not user:
                # Create new user
                user = StreamUser(
                    username=email,
                    email=email,
                    password=hash_password("google_oauth_dummy"),  # Dummy password since nullable=False
                )
                db.add(user)
                db.commit()
                db.refresh(user)

            access_token_expires = timedelta(minutes=get_settings().ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(user.id, user.username, access_token_expires)
            frontend_url = get_settings().FRONTEND_URL
            redirect_url = f"{frontend_url}/login?token={access_token}"
            return RedirectResponse(url=redirect_url)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    return router
