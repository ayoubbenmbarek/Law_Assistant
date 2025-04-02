from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from pydantic import BaseModel
from app.models.user import User, UserCreate, UserResponse, authenticate_user, create_user, get_current_user
from app.models.token import Token, create_access_token

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate = Body(...)):
    """
    Enregistrement d'un nouvel utilisateur.
    """
    try:
        # TODO: Implement actual user registration
        user = await create_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'enregistrement: {str(e)}")

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authentification et génération de token.
    """
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Nom d'utilisateur ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """
    Récupération du profil de l'utilisateur connecté.
    """
    return current_user 