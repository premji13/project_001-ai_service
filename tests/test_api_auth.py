from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.auth as auth
import app.main as main
import app.routers.chatbot as chatbot
from app.database import get_db
from app.models import Base, Document


SECRET = "test-secret-key-with-at-least-32-bytes"


def issue_token(email: str) -> str:
    return jwt.encode(
        {
            "sub": email,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        SECRET,
        algorithm="HS256",
    )


def test_api_routes_require_authentication_and_scope_documents(monkeypatch):
    monkeypatch.setattr(auth, "SECRET_KEY", SECRET)
    monkeypatch.setattr(main, "init_db", lambda: None)
    monkeypatch.setattr(
        chatbot.document_processor,
        "process_file",
        lambda _path: ["chunk"],
    )

    class VectorDB:
        def store_chunks(self, _chunks, _document_id):
            pass

    monkeypatch.setattr(chatbot, "get_vector_db", lambda: VectorDB())

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    test_session = sessionmaker(bind=engine)
    with test_session() as db:
        db.add_all(
            [
                Document(
                    user_email="one@example.com",
                    file_name="one.txt",
                    file_type=".txt",
                ),
                Document(
                    user_email="two@example.com",
                    file_name="two.txt",
                    file_type=".txt",
                ),
            ]
        )
        db.commit()

    def override_get_db():
        with test_session() as db:
            yield db

    main.app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(main.app) as client:
            assert client.get("/").status_code == 200
            assert client.get("/chatbot/documents").status_code == 401
            assert client.post(
                "/chatbot/upload",
                files={"file": ("sample.txt", b"sample", "text/plain")},
            ).status_code == 401
            assert client.post(
                "/chatbot/ask/1",
                json={"question": "question"},
            ).status_code == 401
            assert client.delete("/chatbot/documents/1").status_code == 401

            headers = {
                "Authorization": "Bearer " + issue_token("one@example.com")
            }
            upload = client.post(
                "/chatbot/upload",
                files={"file": ("new.txt", b"sample", "text/plain")},
                headers=headers,
            )
            assert upload.status_code == 200
            documents = client.get("/chatbot/documents", headers=headers)
            assert {document["file_name"] for document in documents.json()} == {
                "one.txt",
                "new.txt",
            }
            assert client.post(
                "/chatbot/ask/2",
                json={"question": "question"},
                headers=headers,
            ).status_code == 404
            assert client.delete(
                "/chatbot/documents/2",
                headers=headers,
            ).status_code == 404
    finally:
        main.app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
