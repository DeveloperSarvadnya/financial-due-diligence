# sec_scraper.py — Fetches SEC EDGAR filings for any public company

import requests
import time
import json
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "FinancialDueDiligence sarvadnya@student.project"
}


def get_company_cik(company_name: str) -> dict | None:
    """
    Search SEC EDGAR for a company by name or ticker symbol.
    Returns a dict with company_name, CIK, and ticker, or None if not found.
    """
    print(f"🔍 Searching SEC EDGAR for: {company_name}")
    
    url = "https://www.sec.gov/files/company_tickers.json"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"❌ Error: SEC returned status code {response.status_code}")
        return None
    
    all_companies = response.json()
    search_term = company_name.lower().strip()
    matches = []
    
    for key, company in all_companies.items():
        name = company.get("title", "").lower()
        ticker = company.get("ticker", "").lower()
        if search_term in name or search_term == ticker:
            matches.append(company)
    
    if not matches:
        print(f"❌ No results found for '{company_name}'")
        return None
    
    best_match = matches[0]
    cik = str(best_match["cik_str"]).zfill(10)
    
    result = {
        "company_name": best_match["title"],
        "cik": cik,
        "ticker": best_match["ticker"],
    }
    
    print(f"✅ Found: {result['company_name']}")
    print(f"   CIK: {cik}")
    print(f"   Ticker: {result['ticker']}")
    
    if len(matches) > 1:
        print(f"\n📋 Other matches found ({len(matches) - 1} more):")
        for m in matches[1:6]:
            print(f"   - {m['title']} ({m['ticker']}) — CIK: {str(m['cik_str']).zfill(10)}")
    
    return result


def get_filings(cik: str, filing_types: list[str] = ["10-K"], count: int = 3) -> list[dict]:
    """
    Fetch recent filings for a CIK from SEC EDGAR submissions API.
    Supports multiple filing types (10-K, 10-Q, 8-K).
    """
    types_str = ", ".join(filing_types)
    print(f"\n📄 Fetching {types_str} filings for CIK: {cik}")
    
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"❌ Error: SEC returned status code {response.status_code}")
        return []
    
    data = response.json()
    recent = data.get("filings", {}).get("recent", {})
    
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accessions = recent.get("accessionNumber", [])
    primary_docs = recent.get("primaryDocument", [])
    descriptions = recent.get("primaryDocDescription", [])
    
    type_counts = {t: 0 for t in filing_types}
    matched_filings = []
    
    for i in range(len(forms)):
        form = forms[i]
        if form in filing_types and type_counts[form] < count:
            accession_no_dashes = accessions[i].replace("-", "")
            doc_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_no_dashes}/{primary_docs[i]}"
            
            filing = {
                "form_type": form,
                "filing_date": dates[i],
                "accession_number": accessions[i],
                "document": primary_docs[i],
                "description": descriptions[i] if i < len(descriptions) else "",
                "url": doc_url,
            }
            matched_filings.append(filing)
            type_counts[form] += 1
    
    if not matched_filings:
        print(f"❌ No {types_str} filings found for this company")
    else:
        print(f"✅ Found {len(matched_filings)} filing(s):\n")
        for f in matched_filings:
            print(f"   📅 {f['filing_date']}  |  {f['form_type']}  |  {f['description']}")
            print(f"   🔗 {f['url']}\n")
    
    return matched_filings


def download_filing_text(url: str) -> str | None:
    """Download an SEC filing and extract clean text using BeautifulSoup."""
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"❌ Error: returned status code {response.status_code}")
        return None
    parsed = BeautifulSoup(response.text, "html.parser")
    return parsed.get_text()


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Testing SEC EDGAR — Full Pipeline")
    print("=" * 60)
    
    company = input("\nEnter a company name to search: ")
    result = get_company_cik(company)
    
    if result:
        print(f"\n📋 Company found: {result}")
        filings = get_filings(
            cik=result["cik"],
            filing_types=["10-K", "10-Q", "8-K"],
            count=2
        )
        if filings:
            from collections import Counter
            counts = Counter(f["form_type"] for f in filings)
            print(f"\n🎉 Successfully retrieved filings for {result['company_name']}!")
            for ftype, fcount in counts.items():
                print(f"   {ftype}: {fcount} filing(s)")
            text = download_filing_text(filings[0]["url"])
            if text:
                print(text[50000:50500])
    else:
        print("\n💡 Tip: Try using the official name (e.g. 'Apple Inc') or ticker (e.g. 'AAPL')")
