from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int | None = None
    email: EmailStr
    token: str | None = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    id: int
    email: EmailStr
    token: str