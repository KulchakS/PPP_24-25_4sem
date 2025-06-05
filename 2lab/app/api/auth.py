from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.cruds.user import create_user, get_user_by_email, verify_password
from app.schemas.user import UserCreate, UserResponse
from app.services.auth import create_access_token, get_current_user
from app.schemas.user import Token

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

@router.post("/sign-up/", response_model=UserResponse)
def sign_up(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")
    new_user = create_user(db, user)
    token = create_access_token(data={"sub": new_user.email})
    return {"email": new_user.email, "token": token}

@router.post("/login/", response_model=Token)
def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={"sub": db_user.email})
    return {"id": db_user.id, "email": db_user.email, "token": token}

@router.get("/users/me/", response_model=UserResponse)
def read_users_me(current_user: UserResponse = Depends(get_current_user)):
    return current_user