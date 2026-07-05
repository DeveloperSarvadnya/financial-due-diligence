# retrieval_chain.py — RAG pipeline: retrieve from ChromaDB + answer with LLM

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from vector_store.chroma_store import query_collection, get_or_create_collection, add_chunks_to_collection
from data_ingestion.sec_scraper import get_company_cik, get_filings
from vector_store.document_processor import process_filing


def retrieve_context(question: str, company_name: str = None, n_results: int = 5) -> str:
    """Query ChromaDB for relevant chunks, optionally filtered by company name."""
    collection = get_or_create_collection()
    where_filter = {"company": company_name} if company_name else None
    results = query_collection(collection, question, n_results, where_filter=where_filter)
    docs = results["documents"][0]
    return "\n\n---\n\n".join(docs)


def build_rag_chain():
    """Create the LCEL chain: prompt | llm | parser."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a senior financial analyst. Answer the question based ONLY on the following context from SEC filings. If the context doesn't contain enough information, say so. Always cite which filing the information comes from."),
        ("human", "Context from SEC filings:\n{context}\n\nQuestion: {question}")
    ])
    llm = ChatOllama(model="llama3.1:8b")
    parser = StrOutputParser()
    return prompt | llm | parser


def ask_question(question: str, company_name: str = None, n_results: int = 5) -> str:
    """Full RAG pipeline: retrieve context → prompt LLM → return grounded answer."""
    print(f"Question: {question}")
    context = retrieve_context(question, company_name=company_name, n_results=n_results)
    print(f"Retrieved {len(context)} characters of context")
    chain = build_rag_chain()
    return chain.invoke({"context": context, "question": question})


def ensure_company_data(company_name: str) -> None:
    """Check if company data exists in ChromaDB; if not, auto-ingest from SEC EDGAR."""
    collection = get_or_create_collection()
    results = collection.get(where={"company": company_name}, limit=1)
    
    if len(results["ids"]) > 0:
        print(f"Data for {company_name} already exists")
        return None
    
    # Auto-ingest: scrape SEC filings and store in ChromaDB
    company_cik = get_company_cik(company_name)
    ticker = company_cik["ticker"]
    print(f"CIK for {company_name}: {company_cik}")
    
    filings = get_filings(company_cik["cik"], filing_types=["10-K"], count=1)
    print(f"\nFound {len(filings)} filings for {company_name}")
    
    processed_chunks = []
    for filing in filings:
        chunks = process_filing(filing, company_name, ticker)
        processed_chunks.extend(chunks)
    
    add_chunks_to_collection(collection, processed_chunks)
    print(f"\n✅ Added {len(processed_chunks)} chunks to collection for {company_name}")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Testing RAG Chain — Ask questions about real SEC filings!")
    print("=" * 60)
    
    company_name = input("Enter company name: ")
    ensure_company_data(company_name)
    
    while True:
        question = input("Ask a question (or type 'quit' to exit): ")
        if question.lower() in ["quit", "exit"]:
            break
        answer = ask_question(question, company_name=company_name)
        print(f"Answer: {answer}")
        print("-" * 60)
