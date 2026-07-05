# competitive_agent.py — Analyzes competitive landscape using SEC filings via RAG

from agents.state import AgentState
from chains.retrieval_chain import ask_question, ensure_company_data
from data_ingestion.sec_scraper import get_company_cik


def competitive_agent(state) -> dict:
    """LangGraph node: performs competitive analysis using 3 targeted RAG queries."""
    company_name = state["company_name"]
    ticker = state["ticker"]

    print(f"🏆 Competitive Agent analyzing {company_name}...")
    ensure_company_data(company_name)

    questions = [
        f"What is {company_name}'s market position and competitive advantages?",
        f"Who are {company_name}'s main competitors and how does it compare?",
        f"What are {company_name}'s key products, services, and growth strategy?"
    ]

    competitive_report = f"## Competitive Analysis for {company_name} ({ticker})\n\n"
    
    for q in questions:
        answer = ask_question(q, company_name=company_name, n_results=10)
        competitive_report += f"### {q}\n\n{answer}\n\n"
    
    print("✅ Competitive Agent complete")
    return {"competitive_analysis": competitive_report}


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Testing Competitive Agent — Standalone")
    print("=" * 60)
    
    company_name = input("Enter the company Name: ")
    company_info = get_company_cik(company_name)
    if not company_info:
        print("❌ Company not found in SEC EDGAR.")
        exit()
    ticker = company_info["ticker"]
    test_state = {"company_name": company_name, "ticker": ticker, "risk_analysis": "", "financial_analysis": "", "competitive_analysis": "", "final_report": ""}
    result = competitive_agent(test_state)
    print(f"\n📄 Competitive Analysis:\n{result['competitive_analysis']}")
