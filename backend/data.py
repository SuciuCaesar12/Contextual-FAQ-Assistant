from langchain_core.embeddings import Embeddings
from langchain_postgres.vectorstores import PGVector
from langchain_community.docstore.document import Document
from typing import Tuple


class DatabaseComponent:
    
    def __init__(self, connection_url: str, embeddings: Embeddings):
        self.vectorstore = PGVector(embeddings=embeddings, connection=connection_url)

    def similarity_search_with_score(self, query: str, k: int = 1) -> Tuple[Document, float]:
        return self.vectorstore.similarity_search_with_score(query=query, k=k)
    
    def add_documents(self, documents: list[Document]):
        return self.vectorstore.add_documents(documents)

