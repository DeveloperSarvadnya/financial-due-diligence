# workflow.py — LangGraph workflow connecting all agents into a pipeline

from langgraph.graph import StateGraph, END
from agents.risk_agent import risk_agent
from agents.financial_agent import financial_agent
from agents.competitive_agent import competitive_agent
from agents.synthesis_agent import synthesis_agent
from agents.state import AgentState
from data_ingestion.sec_scraper import get_company_cik
from dotenv import load_dotenv

load_dotenv()


def build_workflow():
    """Create and compile the LangGraph workflow: Risk → Financial → Competitive → Synthesis → END."""
    state_graph = StateGraph(AgentState)
    
    state_graph.add_node("risk_agent", risk_agent)
    state_graph.add_node("financial_agent", financial_agent)
    state_graph.add_node("competitive_agent", competitive_agent)
    state_graph.add_node("synthesis_agent", synthesis_agent)
    
    state_graph.set_entry_point("risk_agent")
    state_graph.add_edge("risk_agent", "financial_agent")
    state_graph.add_edge("financial_agent", "competitive_agent")
    state_graph.add_edge("competitive_agent", "synthesis_agent")
    state_graph.add_edge("synthesis_agent", END)
    
    print("✅ Workflow: risk → financial → competitive → synthesis → END")
    app = state_graph.compile()
    return app


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Financial Due Diligence — Full Multi-Agent Pipeline")
    print("=" * 60)
    
    company_name = input("Enter the company name: ")
    company_info = get_company_cik(company_name)
    if not company_info:
        print("❌ Company not found in SEC EDGAR. Try the official name or ticker.")
        exit()
    
    ticker = company_info["ticker"]
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
    print(f"\n📄 Risk Analysis:\n{result['risk_analysis']}")
    print(f"\n📄 Financial Analysis:\n{result['financial_analysis']}")
    print(f"\n📄 Competitive Analysis:\n{result['competitive_analysis']}")
    print("\n" + "=" * 60)
    print("📋 FINAL DUE DILIGENCE REPORT")
    print("=" * 60)
    print(result['final_report'])
    print("\n🎉 Full pipeline complete!")
