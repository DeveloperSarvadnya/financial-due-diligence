# news_scraper.py — Fetches recent news about a company using Tavily API

from tavily import TavilyClient
from dotenv import load_dotenv
import os
from vector_store.chroma_store import get_or_create_collection, add_chunks_to_collection
from vector_store.document_processor import chunk_text


def search_company_news(company_name: str, max_results: int = 5) -> list:
    """Search Tavily API for recent financial news about a company."""
    load_dotenv()
    api_key = os.getenv("TAVILY_API_KEY")
    client = TavilyClient(api_key=api_key)
    results = client.search(
        query=f"{company_name} financial news latest developments",
        max_results=max_results,
        search_depth="basic"
    )
    return results["results"]


def ingest_news_to_chromadb(articles: list, company_name: str, ticker: str) -> None:
    """Chunk news articles and store them in ChromaDB with metadata."""
    collection = get_or_create_collection()
    for article_idx, article in enumerate(articles):
        content = article["content"]
        if content and len(content) > 50:
            chunks = chunk_text(content, chunk_size=500, overlap=100)
            processed_chunks = []
            for i, chunk in enumerate(chunks):
                processed_chunks.append({
                    "text": chunk,
                    "metadata": {
                        "source": "news",
                        "company": company_name,
                        "ticker": ticker,
                        "title": article["title"],
                        "url": article["url"],
                        "chunk_index": article_idx * 100 + i
                    }
                })
            add_chunks_to_collection(collection, processed_chunks)
            print(f"✅ Added {len(processed_chunks)} news chunks for {company_name}")


def fetch_and_store_news(company_name: str, ticker: str, max_results: int = 5) -> None:
    """Search news and ingest into ChromaDB in one call."""
    company_news = search_company_news(company_name, max_results)
    if not company_news:
        print("No news found for", company_name)
        return
    ingest_news_to_chromadb(company_news, company_name, ticker)
    print("✅ News ingested for", company_name)


if __name__ == "__main__":
    print("=" * 60)
    print("🗞️ Testing News Scraper — Tavily API")
    print("=" * 60)
    
    from data_ingestion.sec_scraper import get_company_cik
    company_name = input("Enter company name: ")
    company_info = get_company_cik(company_name)
    if not company_info:
        print("❌ Company not found in SEC EDGAR.")
        exit()
    ticker = company_info["ticker"]
    
    articles = search_company_news(company_name)
    print(f"\n📰 Found {len(articles)} articles:")
    for i, article in enumerate(articles, 1):
        print(f"  {i}. {article['title']}")
        print(f"     🔗 {article['url']}\n")
    
    fetch_and_store_news(company_name, ticker)
