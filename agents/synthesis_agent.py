# synthesis_agent.py — Combines all agent analyses into a final due diligence report

from agents.state import AgentState
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser


def synthesis_agent(state) -> dict:
    """LangGraph node: reads all 3 agent outputs and produces a unified report."""
    company_name = state["company_name"]
    ticker = state["ticker"]
    risk_analysis = state["risk_analysis"]
    financial_analysis = state["financial_analysis"]
    competitive_analysis = state["competitive_analysis"]

    print("📝 Synthesis Agent creating final report...")
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "You are a senior due diligence analyst. Combine the following specialist analyses into ONE professional due diligence report. Highlight pros, cons, and red flags. Give an overall confidence score (High/Medium/Low). Format as Markdown."),
        ("human", """
COMPANY: {company_name} ({ticker})

=== RISK ANALYSIS ===
{risk_analysis}

=== FINANCIAL ANALYSIS ===
{financial_analysis}

=== COMPETITIVE ANALYSIS ===
{competitive_analysis}

Create a professional due diligence report with these sections:
1. Executive Summary
2. Key Findings (top 5)
3. Risk Assessment
4. Financial Health
5. Competitive Position
6. Overall Recommendation with confidence score
""")
    ])
    
    llm = ChatOllama(model="llama3.1:8b")
    parser = StrOutputParser()
    chain = prompt_template | llm | parser
    
    final_report = chain.invoke({
        "company_name": company_name,
        "ticker": ticker,
        "risk_analysis": risk_analysis,
        "financial_analysis": financial_analysis,
        "competitive_analysis": competitive_analysis
    })
    
    print("✅ Synthesis Agent complete — Final report ready!")
    return {"final_report": final_report}


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Testing Synthesis Agent — With sample data")
    print("=" * 60)
    
    test_state = {
        "company_name": "Apple",
        "ticker": "AAPL",
        "risk_analysis": "This is a risk analysis for Apple.",
        "financial_analysis": "This is a financial analysis for Apple.",
        "competitive_analysis": "This is a competitive analysis for Apple."
    }
    result = synthesis_agent(test_state)
    print(f"\n📄 Final Report:\n{result['final_report']}")
