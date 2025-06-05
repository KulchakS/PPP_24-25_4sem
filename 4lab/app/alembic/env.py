import os
import sys
from logging.config import fileConfig
from sqlalchemy import create_engine
from alembic import context
from app.core.config import settings
from app.db.base import Base
from app.models.author import Author
from app.models.book import Book

# Добавляем корень проекта в sys.path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..'))

config = context.config
fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_online():
    connectable = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

def run_migrations_offline():
    context.configure(url=settings.DATABASE_URL, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()