"""Q&A engine using Groq LLM and Pinecone retrieval."""
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from app.chatbot.config import GROQ_API_KEY, GROQ_MODEL
from app.chatbot.embeddings import PineconeVectorDB


class RAGQAEngine:
    """RAG-based question answering with Groq and Pinecone."""

    def __init__(self):
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not configured")
        
        self.llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model_name=GROQ_MODEL,
            temperature=0.3,
            max_tokens=1024
        )
        self.vector_db = PineconeVectorDB()

    def answer_question(self, question: str, document_id: str) -> dict:
        """Answer question about a document using RAG."""
        relevant_chunks = self.vector_db.search_chunks(question, document_id)
        
        if not relevant_chunks:
            return {
                "answer": "I could not find relevant information in the document to answer your question.",
                "sources": []
            }
        
        context = "\n\n".join([chunk["text"] for chunk in relevant_chunks])
        
        prompt = PromptTemplate(
            template="""You are a helpful assistant answering questions about a document.
            
Use only the provided context to answer the question. If the information is not in the context, say so.

Context:
{context}

Question: {question}

Answer:""",
            input_variables=["context", "question"]
        )
        
        response = self.llm.invoke(prompt.format(context=context, question=question))
        
        return {
            "answer": response.content,
            "sources": [
                {
                    "chunk_index": chunk["chunk_index"],
                    "relevance_score": chunk["score"]
                }
                for chunk in relevant_chunks[:5]
            ]
        }
