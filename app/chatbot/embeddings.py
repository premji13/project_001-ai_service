"""Embeddings and vector database integration with Pinecone."""
import os
from typing import List
from pinecone import Pinecone, ServerlessSpec
# from langchain_huggingface import HuggingFaceEmbeddings
from openai import OpenAI
from app.chatbot.config import (
    PINECONE_API_KEY, PINECONE_INDEX_NAME, PINECONE_ENVIRONMENT
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_embedding(text: str):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    return response.data[0].embedding

class PineconeVectorDB:
    """Manage Pinecone vector database operations with lightweight embeddings."""

    def __init__(self):
        if not PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY not configured")
        
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        self.index_name = PINECONE_INDEX_NAME
        # Ultra-lightweight embedding model (33MB, 384-dim, optimized for CPU)
        # self.embeddings = HuggingFaceEmbeddings(
        #     model_name="thenlper/gte-small",
        #     cache_folder=None
        # )
        self._ensure_index_exists()

    def _ensure_index_exists(self):
        """Create index if it doesn't exist."""
        indexes = [idx.name for idx in self.pc.list_indexes()]
        if self.index_name not in indexes:
            self.pc.create_index(
                name=self.index_name,
                dimension=384,  # gte-small output dimension
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region=PINECONE_ENVIRONMENT
                )
            )

    def store_chunks(self, chunks: List[str], document_id: str) -> int:
        """Store document chunks in Pinecone."""
        index = self.pc.Index(self.index_name)
        vectors_to_upsert = []
        
        for i, chunk in enumerate(chunks):
            # embedding = self.embeddings.embed_query(chunk)
            embedding = get_embedding(chunk)
            vector_id = f"{document_id}_{i}"
            metadata = {
                "document_id": str(document_id),
                "chunk_index": i,
                "text": chunk[:500]
            }
            vectors_to_upsert.append((vector_id, embedding, metadata))
        
        index.upsert(vectors=vectors_to_upsert)
        return len(vectors_to_upsert)

    def search_chunks(self, query: str, document_id: str, top_k: int = 5) -> List[dict]:
        """Search for relevant chunks."""
        index = self.pc.Index(self.index_name)
        # query_embedding = self.embeddings.embed_query(query)
        query_embedding = get_embedding(query)
        
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            filter={"document_id": {"$eq": str(document_id)}},
            include_metadata=True
        )
        
        return [
            {
                "text": match.metadata.get("text", ""),
                "chunk_index": match.metadata.get("chunk_index", 0),
                "score": match.score
            }
            for match in results.matches
        ]

    def delete_document_vectors(self, document_id: str):
        """Delete all vectors for a document."""
        index = self.pc.Index(self.index_name)
        index.delete(
            filter={"document_id": {"$eq": str(document_id)}}
        )
