# project_001-ai_service

Document chatbot API. The service exposes:

- `POST /chatbot/upload` - upload a `.txt`, `.pdf`, `.doc`, or `.docx` document as multipart form field `file`.
- `GET /chatbot/documents` - list uploaded documents.
- `POST /chatbot/ask/{document_id}` - ask a question with a JSON body such as `{"question": "..."}`.
- `DELETE /chatbot/documents/{document_id}` - delete a document and its stored vectors.

Interactive API documentation is available at `/docs`.

All `/chatbot/*` routes require an `Authorization: Bearer <token>` header. The health endpoint (`GET /`) is public. Tokens must use HS256, include an `exp` expiry, and contain the user's email address in the `sub` claim. The identity service provisions users and issues tokens; this service does not provide registration or login endpoints.

Set `SECRET_KEY` in the deployment environment to the same secret used by the identity service. It must be at least 32 bytes long. Do not commit the secret to source control. The token issuer controls token lifetime; this service validates the `exp` claim.

Document operations are scoped to the authenticated email address. New documents store that email as their owner. Existing documents owned by numeric user IDs are not automatically associated with email addresses and remain inaccessible until assigned to an email.
