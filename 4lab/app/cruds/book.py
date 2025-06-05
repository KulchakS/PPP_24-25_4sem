from sqlalchemy.orm import Session
from app.models.book import Book
from app.schemas.book import BookCreate
from app.cruds.author import get_author

def get_books(db: Session, author_id: int = None, skip: int = 0, limit: int = 100):
    query = db.query(Book)
    if author_id is not None:
        query = query.filter(Book.author_id == author_id)
    return query.offset(skip).limit(limit).all()

def create_book(db: Session, book: BookCreate):
    if not get_author(db, book.author_id):
        return None
    db_book = Book(**book.dict())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book