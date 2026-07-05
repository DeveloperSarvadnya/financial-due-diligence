# risk_agent.py — Analyzes company risks using SEC filings via RAG

from agents.state import AgentState
from chains.retrieval_chain import ask_question, ensure_company_data
from data_ingestion.sec_scraper import get_company_cik


def risk_agent(state) -> dict:
    """LangGraph node: performs risk analysis using 3 targeted RAG queries."""
    company_name = state["company_name"]
    ticker = state["ticker"]
    
    ensure_company_data(company_name)
    
    question1 = f"What are the major risk factors and uncertainties for {company_name}?"
    question2 = f"What legal, regulatory, or compliance risks does {company_name} face?"
    question3 = f"What operational and supply chain risks does {company_name} have?"
    
    answer1 = ask_question(question1, company_name=company_name, n_results=10)
    answer2 = ask_question(question2, company_name=company_name, n_results=10)
    answer3 = ask_question(question3, company_name=company_name, n_results=10)
    
    risk_report = f"""
    ## Risk Analysis for {company_name} ({ticker})
    
    ### Major Risk Factors
    {answer1}
    
    ### Legal & Regulatory Risks
    {answer2}
    
    ### Operational Risks
    {answer3}
    """
    
    print("✅ Risk Agent complete")
    return {"risk_analysis": risk_report}


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Testing Risk Agent — Standalone")
    print("=" * 60)
    
    company_name = input("Enter the company Name: ")
    company_info = get_company_cik(company_name)
    if not company_info:
        print("❌ Company not found in SEC EDGAR. Try the official name or ticker.")
        exit()
    ticker = company_info["ticker"]
    test_state = {"company_name": company_name, "ticker": ticker, "risk_analysis": "", "financial_analysis": "", "competitive_analysis": "", "final_report": ""}
    result = risk_agent(test_state)
    print(f"\n📄 Risk Analysis:\n{result['risk_analysis']}")
