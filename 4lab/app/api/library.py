from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.base import get_db
from app.schemas.author import AuthorCreate, AuthorUpdate, AuthorResponse
from app.schemas.book import BookCreate, BookResponse
from app.cruds.author import get_author, get_authors, create_author, update_author, delete_author
from app.cruds.book import get_books, create_book

router = APIRouter()

# Authors
@router.get("/authors", response_model=List[AuthorResponse])
def read_authors(
    skip: int = Query(0, ge=0, description="Пропустить записи"),
    limit: int = Query(100, ge=1, le=100, description="Ограничить количество записей"),
    db: Session = Depends(get_db)
):
    return get_authors(db, skip=skip, limit=limit)

@router.post("/authors", response_model=AuthorResponse, status_code=status.HTTP_201_CREATED)
def create_new_author(author: AuthorCreate, db: Session = Depends(get_db)):
    return create_author(db, author)

@router.get("/authors/{id}", response_model=AuthorResponse)
def read_author(id: int, db: Session = Depends(get_db)):
    db_author = get_author(db, id)
    if not db_author:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Автор не найден")
    return db_author

@router.put("/authors/{id}", response_model=AuthorResponse)
def update_existing_author(id: int, author: AuthorUpdate, db: Session = Depends(get_db)):
    db_author = update_author(db, id, author)
    if not db_author:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Автор не найден")
    return db_author

@router.delete("/authors/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_author(id: int, db: Session = Depends(get_db)):
    success = delete_author(db, id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Автор не найден")

# Books
@router.get("/books", response_model=List[BookResponse])
def read_books(
    author_id: Optional[int] = Query(None, description="Фильтр по ID автора"),
    skip: int = Query(0, ge=0, description="Пропустить записи"),
    limit: int = Query(100, ge=1, le=100, description="Ограничить количество записей"),
    db: Session = Depends(get_db)
):
    return get_books(db, author_id=author_id, skip=skip, limit=limit)

@router.post("/books", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_new_book(book: BookCreate, db: Session = Depends(get_db)):
    db_book = create_book(db, book)
    if not db_book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Автор не найден")
    return db_book