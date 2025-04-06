from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from loguru import logger

# Load environment variables for security
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key_for_development_only")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security utilities
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/users/token")

# User models
class UserBase(BaseModel):
    email: EmailStr
    name: str
    is_professional: bool = False

class UserCreate(UserBase):
    password: str
    profession: Optional[str] = None
    
class UserInDB(UserBase):
    id: str
    hashed_password: str
    created_at: datetime
    is_active: bool = True
    profession: Optional[str] = None

class User(UserBase):
    id: str
    created_at: datetime
    is_active: bool
    profession: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    name: str
    is_professional: bool
    profession: Optional[str] = None
    created_at: datetime

# User authentication functions
async def get_user_by_email(email: str) -> Optional[UserInDB]:
    """
    Retrieve a user from the database by email.
    This is a placeholder that would connect to your actual database.
    """
    # TODO: Implement actual database lookup
    # Placeholder data for demo
    if email == "test@example.com":
        return UserInDB(
            id="user123",
            email=email,
            name="Test User",
            is_professional=True,
            profession="Avocat",
            hashed_password=pwd_context.hash("password123"),
            created_at=datetime.now(),
            is_active=True
        )
    return None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

async def authenticate_user(email: str, password: str) -> Optional[User]:
    """Authenticate a user with email and password."""
    user = await get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    
    return User(
        id=user.id,
        email=user.email,
        name=user.name,
        is_professional=user.is_professional,
        profession=user.profession,
        created_at=user.created_at,
        is_active=user.is_active
    )

async def create_user(user_data: UserCreate) -> UserResponse:
    """Create a new user."""
    # Check if email already exists
    existing_user = await get_user_by_email(user_data.email)
    if existing_user:
        raise ValueError("Un utilisateur avec cet email existe déjà")
    
    # TODO: Implement actual user creation in database
    # This is just a placeholder
    hashed_password = pwd_context.hash(user_data.password)
    new_user = UserInDB(
        id=f"user_{datetime.now().timestamp()}",
        email=user_data.email,
        name=user_data.name,
        is_professional=user_data.is_professional,
        profession=user_data.profession,
        hashed_password=hashed_password,
        created_at=datetime.now(),
        is_active=True
    )
    
    # Convert to response model
    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        name=new_user.name,
        is_professional=new_user.is_professional,
        profession=new_user.profession,
        created_at=new_user.created_at
    )

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get the current authenticated user from a token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants invalides",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = await get_user_by_email(email)
    if user is None:
        raise credentials_exception
        
    return User(
        id=user.id,
        email=user.email,
        name=user.name,
        is_professional=user.is_professional,
        profession=user.profession,
        created_at=user.created_at,
        is_active=user.is_active
    )

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get the current authenticated user and verify that the account is active.
    This is used as a dependency to protect endpoints that require an active user.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte utilisateur inactif"
        )
    return current_user

async def create_admin_user():
    """
    Create an admin user if it doesn't exist.
    This is used during application startup to ensure there's always an admin account.
    """
    # Check if admin user already exists
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")
    
    admin_user = await get_user_by_email(admin_email)
    if not admin_user:
        logger.info("Création de l'utilisateur admin par défaut")
        try:
            await create_user(UserCreate(
                email=admin_email,
                name="Administrateur",
                password=admin_pass,
                is_professional=True,
                profession="Administrateur"
            ))
            logger.info("Utilisateur admin créé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'utilisateur admin: {str(e)}")
    else:
        logger.info("L'utilisateur admin existe déjà") 