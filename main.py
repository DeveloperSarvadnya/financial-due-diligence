# main.py — Single entry point for the Financial Due Diligence System

from dotenv import load_dotenv
load_dotenv()

from data_ingestion.sec_scraper import get_company_cik
from data_ingestion.news_scraper import fetch_and_store_news
from chains.retrieval_chain import ensure_company_data
from graph.workflow import build_workflow
import os
from datetime import datetime


def main():
    print("=" * 60)
    print("🏦 Autonomous Financial Due Diligence Agent")
    print("=" * 60)
    print()
    
    company_name = input("📌 Enter company name: ").strip()
    if not company_name:
        print("❌ No company name entered.")
        return
    
    # Look up CIK and ticker from SEC EDGAR
    print(f"\n🔍 Looking up {company_name} on SEC EDGAR...")
    company_info = get_company_cik(company_name)
    if not company_info:
        print("❌ Company not found in SEC EDGAR. Try the official name or ticker.")
        return
    
    ticker = company_info["ticker"]
    official_name = company_info["company_name"]
    print(f"✅ Found: {official_name} ({ticker})")
    
    # Ensure SEC filings are in ChromaDB
    print(f"\n📄 Checking SEC filings for {official_name}...")
    ensure_company_data(company_name)
    
    # Fetch and ingest recent news (non-critical — continues on failure)
    print(f"\n🗞️ Fetching recent news for {official_name}...")
    try:
        fetch_and_store_news(company_name, ticker)
    except Exception as e:
        print(f"⚠️ News fetch failed (non-critical): {e}")
        print("   Continuing with SEC filings only...")
    
    # Run the full multi-agent pipeline
    print(f"\n{'=' * 60}")
    print(f"🤖 Running Multi-Agent Analysis for {official_name} ({ticker})")
    print(f"{'=' * 60}")
    print("   🔍 Risk Agent → 📊 Financial Agent → 🏆 Competitive Agent → 📝 Synthesis")
    print()
    
    app = build_workflow()
    initial_state = {
        "company_name": company_name,
        "ticker": ticker,
        "risk_analysis": "",
        "financial_analysis": "",
        "competitive_analysis": "",
        "final_report": ""
    }
    
    result = app.invoke(initial_state)
    
    # Print the final report
    print(f"\n{'=' * 60}")
    print(f"📋 FINAL DUE DILIGENCE REPORT — {official_name} ({ticker})")
    print(f"{'=' * 60}")
    print(result["final_report"])
    
    # Save report to file
    os.makedirs("reports", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"reports/{ticker}_{timestamp}.md"
    
    with open(filename, "w") as f:
        f.write(f"# Due Diligence Report: {official_name} ({ticker})\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        f.write("## Risk Analysis\n\n")
        f.write(result["risk_analysis"])
        f.write("\n\n---\n\n")
        f.write("## Financial Analysis\n\n")
        f.write(result["financial_analysis"])
        f.write("\n\n---\n\n")
        f.write("## Competitive Analysis\n\n")
        f.write(result["competitive_analysis"])
        f.write("\n\n---\n\n")
        f.write("## Final Synthesized Report\n\n")
        f.write(result["final_report"])
    
    print(f"\n💾 Report saved to: {filename}")
    print(f"\n🎉 Due diligence complete for {official_name}!")


if __name__ == "__main__":
    main()
