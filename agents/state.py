# state.py — Shared state schema for all agents (LangGraph TypedDict)

from typing import TypedDict


class AgentState(TypedDict):
    company_name: str
    ticker: str
    risk_analysis: str
    financial_analysis: str
    competitive_analysis: str
    final_report: str
