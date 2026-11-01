# project_001-ai_service

Document chatbot API. The service exposes:

- `POST /chatbot/upload` - upload a `.txt`, `.pdf`, `.doc`, or `.docx` document as multipart form field `file`.
- `GET /chatbot/documents` - list uploaded documents.
- `POST /chatbot/ask/{document_id}` - ask a question with a JSON body such as `{"question": "..."}`.
- `DELETE /chatbot/documents/{document_id}` - delete a document and its stored vectors.

Interactive API documentation is available at `/docs`.

These endpoints are unauthenticated, and document operations are shared across clients.
On startup, the legacy `documents.user_id` column is removed.
