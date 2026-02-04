from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from jose import JWTError

from app.infrastructure.database import get_db
from app.services.auth_service import AuthService
from app.domain.user import User, UserCreate, UserLogin, Token
from app.infrastructure.auth import decode_refresh_token
from app.api.dependencies import get_current_user
from app.config import settings
import logging

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=dict)
async def register(
    user_data: UserCreate,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account.
    
    - Validates email format and uniqueness
    - Validates password strength
    - Creates user and companion context
    - Issues access and refresh tokens
    - Sets HTTP-only cookie for refresh token
    """
    service = AuthService(db)
    user, access_token, refresh_token = await service.register_user(user_data)
    
    # Set refresh token as HTTP-only cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",  # Changed from 'strict' to allow cookies in dev
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # seconds
        path="/",  # Explicitly set path
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/login", response_model=dict)
async def login(
    credentials: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password.
    
    - Validates credentials
    - Issues new access and refresh tokens
    - Sets HTTP-only cookie for refresh token
    """
    service = AuthService(db)
    user, access_token, refresh_token = await service.login_user(credentials)
    
    # Set refresh token as HTTP-only cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",  # Changed from 'strict' to allow cookies in dev
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",  # Explicitly set path
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


from app.domain.user import UserGoogleLogin

@router.post("/google", response_model=dict)
async def google_login(
    login_data: UserGoogleLogin,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with Google.
    
    - Verifies Google ID Token
    - Creates or Finds user
    - Issues tokens
    """
    logger.info("Google login endpoint called")
    try:
        service = AuthService(db)
        user, access_token, refresh_token = await service.register_or_login_google_user(login_data.credential)
        
        # Set refresh token as HTTP-only cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            path="/",
        )
        
        logger.info(f"Successfully logged in Google user: {user.email}")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
    except Exception as e:
        logger.error(f"Error in google_login: {str(e)}", exc_info=True)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during Google login: {str(e)}"
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token from HTTP-only cookie.
    
    - Validates refresh token
    - Implements token rotation (single-use tokens)
    - Detects token theft (reuse of revoked tokens)
    - Issues new access and refresh tokens
    """
    logger.info("Refresh token endpoint called")
    try:
        logger.debug(f"Refresh token from cookie: {refresh_token[:20] if refresh_token else 'None'}...")
        
        if not refresh_token:
            logger.warning("Refresh token not found in cookies")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        try:
            # Decode refresh token
            payload = decode_refresh_token(refresh_token)
            user_id_str = payload.get("sub")
            token_family = payload.get("family")
            
            if not user_id_str or not token_family:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            from uuid import UUID
            user_id = UUID(user_id_str)
            
        except (JWTError, ValueError) as e:
            logger.error(f"Failed to decode refresh token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Refresh tokens (with rotation and theft detection)
        service = AuthService(db)
        new_access_token, new_refresh_token = await service.refresh_access_token(
            token_family, user_id
        )
        
        # Set new refresh token as HTTP-only cookie
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",  # Changed from 'strict' to allow cookies in dev
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            path="/",  # Explicitly set path
        )
        
        logger.info(f"Successfully refreshed token for user {user_id}")
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
    except Exception as e:
        logger.error(f"Error in refresh_token: {str(e)}", exc_info=True)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during token refresh: {str(e)}"
        )


@router.post("/logout")
async def logout(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout current user.
    
    - Revokes refresh token
    - Clears HTTP-only cookie
    """
    if refresh_token:
        try:
            payload = decode_refresh_token(refresh_token)
            token_family = payload.get("family")
            
            if token_family:
                service = AuthService(db)
                await service.revoke_refresh_token(token_family)
        except JWTError:
            pass  # Token already invalid, just clear cookie
    
    # Clear refresh token cookie
    response.delete_cookie(key="refresh_token")
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=User)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user's profile.
    
    Requires valid access token.
    """
    return current_user


class UpdateLanguageRequest(BaseModel):
    """Request to update user language."""
    language: str  # "en" or "es"


@router.patch("/me/language", response_model=User)
async def update_user_language(
    request: UpdateLanguageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user's language preference.
    
    Supported languages: en, es
    """
    from sqlalchemy import update
    from app.infrastructure.tables import UserModel
    
    # Validate language
    if request.language not in ["en", "es"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported language. Use 'en' or 'es'."
        )
    
    # Update user language
    stmt = (
        update(UserModel)
        .where(UserModel.id == current_user.id)
        .values(language=request.language)
    )
    await db.execute(stmt)
    await db.commit()
    
    # Fetch updated user
    from sqlalchemy import select
    result = await db.execute(select(UserModel).where(UserModel.id == current_user.id))
    updated_user = result.scalar_one()
    
    logger.info(f"Updated language to {request.language} for user {current_user.id}")
    return updated_user


from app.domain.user import OnboardingData

@router.post("/onboarding", response_model=User)
async def complete_onboarding(
    data: OnboardingData,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Complete user onboarding and save profile data.
    
    Saves:
    - Language preference
    - Full name
    - Professional role
    - Years of experience
    - Primary stressor
    - Coping style
    - Sets onboarding_completed flag to True
    """
    from sqlalchemy import update
    from app.infrastructure.tables import UserModel
    
    # Update user with onboarding data
    stmt = (
        update(UserModel)
        .where(UserModel.id == current_user.id)
        .values(
            language=data.language,
            full_name=data.full_name,
            professional_role=data.professional_role,
            years_experience=data.years_experience,
            primary_stressor=data.primary_stressor,
            coping_style=data.coping_style,
            onboarding_completed=True
        )
    )
    await db.execute(stmt)
    await db.commit()
    
    # Fetch updated user
    from sqlalchemy import select
    result = await db.execute(select(UserModel).where(UserModel.id == current_user.id))
    updated_user = result.scalar_one()
    
    logger.info(f"Completed onboarding for user {current_user.id} - Role: {data.professional_role}, Lang: {data.language}")
    return updated_user

