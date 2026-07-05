# chroma_store.py — ChromaDB operations: embed, store, and query document chunks

import chromadb
from langchain_ollama import OllamaEmbeddings


def get_embedding_function():
    """Return the embedding function configured with nomic-embed-text."""
    return OllamaEmbeddings(model="nomic-embed-text")


def get_or_create_collection(collection_name: str = "sec_filings"):
    """Get or create a ChromaDB collection with cosine similarity."""
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    print(f"✅ Collection '{collection_name}' ready ({collection.count()} documents)")
    return collection


def add_chunks_to_collection(collection, processed_chunks: list[dict]):
    """Embed and store processed chunks in ChromaDB."""
    embedding = get_embedding_function()
    documents = []
    metadatas = []
    ids = []
    
    for chunk in processed_chunks:
        documents.append(chunk["text"])
        metadatas.append(chunk["metadata"])
        # Flexible ID: uses form_type for SEC filings, source for news
        chunk_type = chunk['metadata'].get('form_type', chunk['metadata'].get('source', 'unknown'))
        ids.append(f"{chunk['metadata']['ticker']}_{chunk_type}_{chunk['metadata']['chunk_index']}")
    
    embeddings = embedding.embed_documents(documents)
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids,
        embeddings=embeddings
    )
    print(f"✅ Added {len(processed_chunks)} chunks to collection. Total documents: {collection.count()}")


def query_collection(collection, query: str, n_results: int = 5, where_filter: dict = None):
    """Semantic search over the collection with optional metadata filter."""
    embedding = get_embedding_function()
    query_embedding = embedding.embed_query(query)
    query_args = {
        "query_embeddings": [query_embedding],
        "n_results": n_results
    }
    if where_filter:
        query_args["where"] = where_filter
    return collection.query(**query_args)


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Testing ChromaDB Store — Full Pipeline")
    print("=" * 60)
    
    from vector_store.document_processor import process_filing
    from data_ingestion.sec_scraper import get_company_cik, get_filings
    
    company_name = input("Enter the Company Name: ")
    company_cik = get_company_cik(company_name)
    if not company_cik:
        print("❌ Company not found.")
        exit()
    
    filings = get_filings(company_cik["cik"], filing_types=["10-K"], count=1)
    if not filings:
        print("❌ No 10-K filings found.")
        exit()
    
    document_filings = process_filing(filings[0], company_name, company_cik["ticker"])
    collection = get_or_create_collection()
    add_chunks_to_collection(collection, document_filings)
    
    results = query_collection(collection, "What are the main risks?", n_results=5)
    print(results)
    print("\n🎉 ChromaDB pipeline test complete!")
