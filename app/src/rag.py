"""RAG: load files from data/docs, chunk, embed, store, retrieve.
Local = Chroma on disk. Cloud = Azure AI Search. Switch with VECTOR_STORE."""
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from . import config as c
from .llm import embeddings


def load_documents(folder: str) -> list[Document]:
    docs = []
    for p in sorted(Path(folder).glob("**/*")):
        if p.suffix.lower() in {".md", ".txt"}:
            docs.append(Document(page_content=p.read_text(encoding="utf-8"), metadata={"source": p.name}))
    return docs


def chunk(docs: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    return splitter.split_documents(docs)


def get_store():
    if c.VECTOR_STORE == "azure_search":
        from langchain_community.vectorstores.azuresearch import AzureSearch
        return AzureSearch(azure_search_endpoint=c.SEARCH_ENDPOINT, azure_search_key=c.SEARCH_KEY or None,
                           index_name=c.SEARCH_INDEX, embedding_function=embeddings().embed_query)
    from langchain_community.vectorstores import Chroma
    return Chroma(collection_name="fai", persist_directory=c.CHROMA_DIR, embedding_function=embeddings())


def ingest(folder: str | None = None) -> int:
    repo_docs = Path(__file__).resolve().parents[2] / "data" / "docs"
    path = folder or (str(repo_docs) if repo_docs.exists() else "data/docs")
    chunks = chunk(load_documents(path))
    if chunks:
        get_store().add_documents(chunks)
    return len(chunks)


def retrieve(query: str, k: int = 4) -> list[Document]:
    return get_store().similarity_search(query, k=k)

def retrieve_relevant(query: str, k: int = 4) -> list[Document]:
    """Only return passages that are actually close to the question."""
    pairs = get_store().similarity_search_with_relevance_scores(query, k=k)
    return [d for d, score in pairs if score >= c.MIN_RELEVANCE]