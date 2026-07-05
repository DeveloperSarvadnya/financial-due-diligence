# document_processor.py — Cleans, chunks, and prepares filing text for embedding

import re
from data_ingestion.sec_scraper import download_filing_text, get_company_cik, get_filings


def clean_text(raw_text: str) -> str:
    """Remove XBRL tags, normalize whitespace, and strip junk from raw filing text."""
    clean = re.sub(r'\S+:\S+', "", raw_text)        # Remove XBRL-style tags
    clean = re.sub(r'\n{3,}', "\n\n", clean)         # Collapse excess newlines
    clean = re.sub(r' {2,}', " ", clean)              # Collapse excess spaces
    return clean.strip()


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Split text into overlapping chunks using a sliding window."""
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + chunk_size])
        start += (chunk_size - overlap)
    return chunks


def process_filing(filing: dict, company_name: str, ticker: str) -> list[dict]:
    """
    Full pipeline: download filing → clean → chunk → attach metadata.
    Returns a list of processed chunks ready for ChromaDB.
    """
    raw_text = download_filing_text(filing["url"])
    if not raw_text:
        print("Filing is empty")
        return []
    
    cleaned = clean_text(raw_text)
    chunked_text = chunk_text(cleaned)
    processed_chunks = []
    
    for i, chunk in enumerate(chunked_text):
        processed_chunks.append({
            "text": chunk,
            "metadata": {
                "source": "SEC EDGAR",
                "company": company_name,
                "ticker": ticker,
                "form_type": filing["form_type"],
                "filing_date": filing["filing_date"],
                "chunk_index": i,
                "url": filing["url"]
            }
        })
    
    print(f"Successfully processed {len(processed_chunks)} chunks from {ticker} {filing['form_type']} ({filing['filing_date']})")
    return processed_chunks


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Testing Document Processor — Full Pipeline")
    print("=" * 60)
    
    company = input("Enter Company Name: ")
    company_cik = get_company_cik(company)
    filings = get_filings(company_cik["cik"], filing_types=["10-K"], count=1)
    ticker = company_cik["ticker"]
    processed_chunks = process_filing(filings[0], company, ticker)
    
    print(f"Total chunks: {len(processed_chunks)}")
    print("\nFirst chunk:")
    print(processed_chunks[0]["text"][:300])
    print("\nFirst chunk metadata:")
    print(processed_chunks[0]["metadata"])
