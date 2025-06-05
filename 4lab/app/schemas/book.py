from pydantic import BaseModel, validator
from datetime import datetime

class BookBase(BaseModel):
    title: str
    year: int
    author_id: int

class BookCreate(BookBase):
    @validator("year")
    def validate_year(cls, value):
        current_year = datetime.now().year
        if value > current_year:
            raise ValueError("Год издания не может быть в будущем")
        return value

class BookResponse(BookBase):
    id: int

    class Config:
        from_attributes = True