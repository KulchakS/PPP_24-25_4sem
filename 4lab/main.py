from fastapi import FastAPI
from app.api.library import router

app = FastAPI()

app.include_router(router)