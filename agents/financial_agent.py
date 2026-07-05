# financial_agent.py — Analyzes financial metrics using SEC filings via RAG

from agents.state import AgentState
from chains.retrieval_chain import ask_question, ensure_company_data
from data_ingestion.sec_scraper import get_company_cik


def financial_agent(state) -> dict:
    """LangGraph node: performs financial analysis using 3 targeted RAG queries."""
    company_name = state["company_name"]
    ticker = state["ticker"]

    print(f"📊 Financial Agent analyzing {company_name}...")
    ensure_company_data(company_name)

    questions = [
        f"What are {company_name}'s total revenue, net income, and key financial metrics?",
        f"What are {company_name}'s profit margins, operating expenses, and cost structure?",
        f"What is {company_name}'s debt, cash position, and liquidity outlook?"
    ]

    financial_report = f"## Financial Analysis for {company_name} ({ticker})\n\n"
    
    for q in questions:
        answer = ask_question(q, company_name=company_name, n_results=10)
        financial_report += f"### {q}\n\n{answer}\n\n"
    
    print("✅ Financial Agent complete")
    return {"financial_analysis": financial_report}


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Testing Financial Agent — Standalone")
    print("=" * 60)
    
    company_name = input("Enter the company Name: ")
    company_info = get_company_cik(company_name)
    if not company_info:
        print("❌ Company not found in SEC EDGAR.")
        exit()
    ticker = company_info["ticker"]
    test_state = {"company_name": company_name, "ticker": ticker, "risk_analysis": "", "financial_analysis": "", "competitive_analysis": "", "final_report": ""}
    result = financial_agent(test_state)
    print(f"\n📄 Financial Analysis:\n{result['financial_analysis']}")
