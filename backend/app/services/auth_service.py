from datetime import datetime, timedelta
from uuid import UUID, uuid4
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status

from app.domain.user import User, UserCreate, UserLogin
from app.infrastructure.tables import UserModel, RefreshTokenModel, CompanionContextModel
from app.infrastructure.auth import (
    get_password_hash,
    verify_password,
    validate_password_strength,
    create_access_token,
    create_refresh_token,
)
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Service for user authentication and token management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def register_user(self, data: UserCreate) -> tuple[User, str, str]:
        """
        Register a new user and create their companion context.
        
        Args:
            data: User registration data
            
        Returns:
            Tuple of (user, access_token, refresh_token)
            
        Raises:
            HTTPException: If email exists or password is weak
        """
        # Validate password strength
        is_valid, error_msg = validate_password_strength(data.password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Check if email already exists
        result = await self.db.execute(
            select(UserModel).where(UserModel.email == data.email)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user
        hashed_password = get_password_hash(data.password)
        user_model = UserModel(
            email=data.email,
            hashed_password=hashed_password,
            full_name=data.full_name,
        )
        self.db.add(user_model)
        await self.db.flush()  # Get user ID
        
        # Create companion context for user
        context = CompanionContextModel(user_id=user_model.id)
        self.db.add(context)
        
        await self.db.commit()
        await self.db.refresh(user_model)
        
        # Generate tokens
        token_family = str(uuid4())
        access_token = create_access_token(user_model.id)
        refresh_token = create_refresh_token(user_model.id, token_family)
        
        # Store refresh token
        await self._store_refresh_token(user_model.id, token_family)
        await self.db.commit()
        
        logger.info(f"Registered new user {user_model.id} with token_family {token_family}")
        
        user = User.model_validate(user_model)
        return user, access_token, refresh_token
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user with email and password.
        
        Args:
            email: User's email
            password: Plain text password
            
        Returns:
            User object if authenticated, None otherwise
        """
        result = await self.db.execute(
            select(UserModel).where(UserModel.email == email)
        )
        user_model = result.scalar_one_or_none()
        
        if not user_model:
            return None
        
        if not verify_password(password, user_model.hashed_password):
            return None
        
        if not user_model.is_active:
            return None
        
        return User.model_validate(user_model)
    
    async def login_user(self, data: UserLogin) -> tuple[User, str, str]:
        """
        Login user and issue tokens.
        
        Args:
            data: Login credentials
            
        Returns:
            Tuple of (user, access_token, refresh_token)
            
        Raises:
            HTTPException: If credentials are invalid
        """
        user = await self.authenticate_user(data.email, data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Generate new token family
        token_family = str(uuid4())
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id, token_family)
        
        # Store refresh token
        await self._store_refresh_token(user.id, token_family)
        await self.db.commit()
        
        logger.info(f"User {user.id} logged in with new token_family {token_family}")
        
        return user, access_token, refresh_token
    
    async def refresh_access_token(self, token_family: str, user_id: UUID) -> tuple[str, str]:
        """
        Refresh access token using refresh token rotation.
        
        Args:
            token_family: Current token family ID
            user_id: User's UUID
            
        Returns:
            Tuple of (new_access_token, new_refresh_token)
            
        Raises:
            HTTPException: If token is revoked (theft detected) or invalid
        """
        logger.info(f"Attempting to refresh token for user_id={user_id}, token_family={token_family}")
        
        # Check if token family exists and is not revoked
        result = await self.db.execute(
            select(RefreshTokenModel).where(
                RefreshTokenModel.token_family == token_family,
                RefreshTokenModel.user_id == user_id
            )
        )
        token_record = result.scalar_one_or_none()
        
        logger.debug(f"Database lookup result: token_record={'Found' if token_record else 'NOT FOUND'}")
        
        if not token_record:
            logger.error(f"Token family '{token_family}' not found in database for user {user_id}")
            # Let's check if ANY tokens exist for this user
            all_tokens_result = await self.db.execute(
                select(RefreshTokenModel).where(RefreshTokenModel.user_id == user_id)
            )
            all_tokens = all_tokens_result.scalars().all()
            logger.error(f"User {user_id} has {len(all_tokens)} total refresh tokens in DB")
            for token in all_tokens:
                logger.error(f"  - family: {token.token_family}, revoked: {token.is_revoked}, expires: {token.expires_at}")
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # THEFT DETECTION: If token is already revoked, someone is reusing it
        if token_record.is_revoked:
            # Revoke all tokens for this user (security breach)
            await self.revoke_all_user_tokens(user_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token reuse detected. All sessions have been revoked.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check expiration
        if token_record.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Revoke old token (single-use)
        await self.db.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.id == token_record.id)
            .values(is_revoked=True)
        )
        
        # Create new token family (rotation)
        new_token_family = str(uuid4())
        new_access_token = create_access_token(user_id)
        new_refresh_token = create_refresh_token(user_id, new_token_family)
        
        # Store new refresh token
        await self._store_refresh_token(user_id, new_token_family)
        
        await self.db.commit()
        
        return new_access_token, new_refresh_token
    
    async def revoke_refresh_token(self, token_family: str) -> None:
        """
        Revoke a specific refresh token family.
        
        Args:
            token_family: Token family to revoke
        """
        await self.db.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.token_family == token_family)
            .values(is_revoked=True)
        )
        await self.db.commit()
    
    async def revoke_all_user_tokens(self, user_id: UUID) -> None:
        """
        Revoke all refresh tokens for a user (logout all sessions).
        
        Args:
            user_id: User's UUID
        """
        await self.db.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.user_id == user_id)
            .values(is_revoked=True)
        )
        await self.db.commit()
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User's UUID
            
        Returns:
            User object or None
        """
        result = await self.db.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        user_model = result.scalar_one_or_none()
        
        if not user_model:
            return None
        
        return User.model_validate(user_model)
    
    async def _store_refresh_token(self, user_id: UUID, token_family: str) -> None:
        """
        Store refresh token metadata in database.
        
        Args:
            user_id: User's UUID
            token_family: Token family ID
        """
        expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        token_record = RefreshTokenModel(
            user_id=user_id,
            token_family=token_family,
            expires_at=expires_at
        )
        self.db.add(token_record)
        logger.debug(f"Stored refresh token for user {user_id}, family {token_family}, expires {expires_at}")
    
    async def cleanup_expired_tokens(self) -> int:
        """
        Remove expired refresh tokens from database.
        Background task for maintenance.
        
        Returns:
            Number of tokens deleted
        """
        result = await self.db.execute(
            select(RefreshTokenModel).where(
                RefreshTokenModel.expires_at < datetime.utcnow()
            )
        )
        expired_tokens = result.scalars().all()
        
        for token in expired_tokens:
            await self.db.delete(token)
        
        await self.db.commit()
        return len(expired_tokens)

    async def register_or_login_google_user(self, credential: str) -> tuple[User, str, str]:
        """
        Authenticate user via Google OAuth 2.0.
        
        Args:
            credential: JWT ID token from Google
            
        Returns:
            Tuple of (user, access_token, refresh_token)
        """
        import httpx
        
        # 1. Verify Token with Google
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}",
                    timeout=10.0
                )
                resp.raise_for_status()
                google_data = resp.json()
            except Exception as e:
                logger.error(f"Google Token Verification Failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Google credentials"
                )
        
        # 2. Check Audience (Client ID)
        if google_data.get("aud") != settings.GOOGLE_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google Client ID"
            )
            
        google_id = google_data["sub"]
        email = google_data["email"]
        name = google_data.get("name", "Google User")
        
        # 3. Find User (by google_id OR email)
        result = await self.db.execute(
            select(UserModel).where(
                (UserModel.google_id == google_id) | (UserModel.email == email)
            )
        )
        user_model = result.scalar_one_or_none()
        
        if user_model:
            # Update google_id if missing (Link account)
            if not user_model.google_id:
                user_model.google_id = google_id
                user_model.auth_provider = "google" # Switch or add marker
                self.db.add(user_model)
                await self.db.commit()
                await self.db.refresh(user_model)
        else:
            # Create new user
            # Generate a random strong password (user won't use it, but DB needs it)
            random_pw = str(uuid4()) + str(uuid4())
            hashed_password = get_password_hash(random_pw)
            
            user_model = UserModel(
                email=email,
                hashed_password=hashed_password,
                full_name=name,
                google_id=google_id,
                auth_provider="google",
                is_active=True
            )
            self.db.add(user_model)
            await self.db.flush()
            
            # Create context
            context = CompanionContextModel(user_id=user_model.id)
            self.db.add(context)
            
            await self.db.commit()
            await self.db.refresh(user_model)
            
        # 4. Generate Tokens
        token_family = str(uuid4())
        access_token = create_access_token(user_model.id)
        refresh_token = create_refresh_token(user_model.id, token_family)
        
        await self._store_refresh_token(user_model.id, token_family)
        await self.db.commit()
        
        return User.model_validate(user_model), access_token, refresh_token
