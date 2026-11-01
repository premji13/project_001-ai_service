from pydantic import BaseModel, Field
from datetime import datetime

class DocumentResponse(BaseModel):
    id: int
    file_name: str
    file_type: str
    chunk_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    message: str
    document: DocumentResponse


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)


class AnswerResponse(BaseModel):
    answer: str
    sources: list[dict]
