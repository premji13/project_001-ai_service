from fastapi import FastAPI
from app.database import init_db
from app.routers import chatbot_router

app = FastAPI(title="User API", version="1.0.0")

@app.on_event("startup")
async def startup():
    init_db()

@app.get('/')
def home():
    return {'msg': 'Welcome to the User API. Use /docs for API documentation.'}

app.include_router(chatbot_router)
