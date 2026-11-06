"""Chatbot API endpoints for document upload and Q&A."""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Path, Body
from sqlalchemy.orm import Session
from app.auth import get_current_user_email
from app.database import get_db
from app.models import Document
from app.schemas import DocumentUploadResponse, DocumentResponse, QuestionRequest, AnswerResponse
from app.chatbot.config import MAX_FILE_SIZE, ALLOWED_EXTENSIONS
from app.chatbot.document_processor import DocumentProcessor
from app.chatbot.embeddings import PineconeVectorDB
from app.chatbot.qa_engine import RAGQAEngine
import os
import tempfile

router = APIRouter(
    prefix="/chatbot",
    tags=["chatbot"],
    dependencies=[Depends(get_current_user_email)],
)
document_processor = DocumentProcessor()

_vector_db = None
_qa_engine = None


def get_vector_db():
    """Lazy load vector DB."""
    global _vector_db
    if _vector_db is None:
        _vector_db = PineconeVectorDB()
    return _vector_db


def get_qa_engine():
    """Lazy load QA engine."""
    global _qa_engine
    if _qa_engine is None:
        _qa_engine = RAGQAEngine()
    return _qa_engine


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    user_email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db)
):
    """Upload and process a document (txt, pdf, docx, doc)."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")

    _, ext = os.path.splitext(file.filename)
    if ext.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    tmp_path = None
    try:
        vector_db = get_vector_db()

        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        # Process file
        chunks = document_processor.process_file(tmp_path)

        # Store document in DB
        doc = Document(
            user_email=user_email,
            file_name=file.filename,
            file_type=ext.lower(),
            chunk_count=len(chunks)
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Store embeddings in Pinecone
        vector_db.store_chunks(chunks, str(doc.id))

        return DocumentUploadResponse(
            message=f"Document '{file.filename}' uploaded and processed ({len(chunks)} chunks)",
            document=DocumentResponse.model_validate(doc)
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.get("/documents", response_model=list[DocumentResponse])
async def list_documents(
    user_email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db),
):
    """List all uploaded documents."""
    documents = db.query(Document).filter(Document.user_email == user_email).all()
    return documents


@router.post("/ask/{document_id}", response_model=AnswerResponse)
async def ask_question(
    document_id: int = Path(..., gt=0),
    request: QuestionRequest = Body(...),
    user_email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db)
):
    """Ask a question about a specific document."""
    if request is None or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question is required")

    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_email == user_email)
        .first()
    )

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        qa_engine = get_qa_engine()
        response = qa_engine.answer_question(request.question, str(document_id))
        return AnswerResponse(**response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error answering question: {str(e)}")


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int = Path(..., gt=0),
    user_email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db)
):
    """Delete a document and its embeddings from Pinecone."""
    
    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_email == user_email)
        .first()
    )
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        vector_db = get_vector_db()
        # Remove from vector DB
        vector_db.delete_document_vectors(str(document_id))
        
        # Remove from DB
        db.delete(doc)
        db.commit()
        
        return {"message": f"Document '{doc.file_name}' deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")
