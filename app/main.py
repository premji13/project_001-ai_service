from fastapi import FastAPI
from app.auth import validate_auth_configuration
from app.database import init_db
from app.routers import chatbot_router

app = FastAPI(
    title="Chatbot API",
    version="1.0.0",
)

@app.on_event("startup")
async def startup():
    validate_auth_configuration()
    init_db()

@app.get('/')
async def health():
    return {'message':'Welcome !'}

app.include_router(chatbot_router)
