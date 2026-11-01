from fastapi import FastAPI
from app.database import init_db
from app.routers import chatbot_router

app = FastAPI(title="Chatbot API", version="1.0.0")

@app.on_event("startup")
async def startup():
    init_db()

@app.get('/')
async def health():
    return {'message':'Welcome !'}

app.include_router(chatbot_router)
