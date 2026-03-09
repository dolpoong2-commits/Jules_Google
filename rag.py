import os
from typing import List, Dict, Any

from langchain_community.document_loaders import PyPDFLoader, TextLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import chromadb

# Initialize ChromaDB client persistent storage
CHROMA_PERSIST_DIR = os.path.join(os.getcwd(), "chroma_db")

# Initialize embedding model suitable for Korean
# "jhgan/ko-sroberta-multitask" is a popular, lightweight model for Korean semantics
# "BAAI/bge-m3" is heavier but excellent for multilingual. We'll default to the lightweight one.
DEFAULT_EMBEDDING_MODEL = "jhgan/ko-sroberta-multitask"

class RAGManager:
    def __init__(self, embedding_model_name: str = DEFAULT_EMBEDDING_MODEL):
        self.embedding_model_name = embedding_model_name
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model_name,
            model_kwargs={'device': 'cpu'}, # Use CPU by default for embeddings to save VRAM for LLM
            encode_kwargs={'normalize_embeddings': True}
        )

        # Collection for external documents (Data Sheets, PDFs, etc.)
        self.docs_vectorstore = Chroma(
            collection_name="external_docs",
            embedding_function=self.embeddings,
            persist_directory=CHROMA_PERSIST_DIR
        )

        # Collection for past chat history
        self.history_vectorstore = Chroma(
            collection_name="chat_history",
            embedding_function=self.embeddings,
            persist_directory=CHROMA_PERSIST_DIR
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            length_function=len
        )

    def ingest_document(self, file_path: str, tags: str = "") -> int:
        """Loads a document, splits it, and adds it to the ChromaDB."""
        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.pdf':
            loader = PyPDFLoader(file_path)
        elif ext == '.txt':
            loader = TextLoader(file_path, encoding='utf-8')
        elif ext == '.csv':
            loader = CSVLoader(file_path, encoding='utf-8')
        else:
            raise ValueError(f"Unsupported file extension: {ext}")

        documents = loader.load()
        chunks = self.text_splitter.split_documents(documents)

        # Add metadata tags
        for chunk in chunks:
            chunk.metadata["source"] = os.path.basename(file_path)
            chunk.metadata["tags"] = tags

        # Add to vector store
        if chunks:
            self.docs_vectorstore.add_documents(chunks)

        return len(chunks)

    def ingest_chat_message(self, session_id: str, role: str, content: str, tags: str = ""):
        """Indexes a chat message for future retrieval."""
        # We wrap the text in Langchain's Document object
        from langchain_core.documents import Document

        doc = Document(
            page_content=f"{role.capitalize()}: {content}",
            metadata={
                "session_id": session_id,
                "role": role,
                "tags": tags,
                "source": "chat_history"
            }
        )
        self.history_vectorstore.add_documents([doc])

    def retrieve_context(self, query: str, k: int = 3, use_docs: bool = True, use_history: bool = True) -> str:
        """Retrieves relevant contexts from both documents and past history based on the query."""
        retrieved_texts = []

        if use_docs:
            docs_results = self.docs_vectorstore.similarity_search(query, k=k)
            for doc in docs_results:
                retrieved_texts.append(f"[Document - {doc.metadata.get('source', 'Unknown')}]: {doc.page_content}")

        if use_history:
            history_results = self.history_vectorstore.similarity_search(query, k=k)
            for doc in history_results:
                retrieved_texts.append(f"[Past Chat - Session {doc.metadata.get('session_id', 'Unknown')}]: {doc.page_content}")

        # Combine the context
        if not retrieved_texts:
            return ""

        return "\n\n".join(retrieved_texts)

    def get_document_stats(self) -> Dict[str, Any]:
        """Returns statistics about the vector database."""
        try:
            doc_count = self.docs_vectorstore._collection.count()
            history_count = self.history_vectorstore._collection.count()
            return {
                "document_chunks": doc_count,
                "history_chunks": history_count
            }
        except Exception:
            return {"document_chunks": 0, "history_chunks": 0}
