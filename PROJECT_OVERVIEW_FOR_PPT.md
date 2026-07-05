# PROJECT OVERVIEW — Financial Due Diligence Agent
## For Slide/Presentation Generation

---

## SLIDE 1: Title

**Autonomous Financial Due Diligence Agent**

*Multi-agent AI system that generates professional due diligence reports from SEC filings and real-time news*

Built with: LangChain · LangGraph · ChromaDB · Ollama · Llama 3.1

---

## SLIDE 2: Problem Statement

- Investment banks spend **200–400 hours per deal** on manual due diligence
- Analysts manually read hundreds of pages of SEC 10-K filings
- Cross-referencing risk factors, financials, and competitive data is tedious and error-prone
- Reports are often outdated by the time they're completed
- The process hasn't changed significantly despite advances in AI

**The question:** Can we automate the intelligence-gathering phase of financial due diligence?

---

## SLIDE 3: Solution — What This Project Does

- User types **one company name** (e.g., "Alphabet")
- System **automatically**:
  - Scrapes official SEC EDGAR filings (10-K annual reports)
  - Fetches real-time financial news
  - Runs 4 specialized AI agents
  - Generates a structured due diligence report
- Report includes: risk analysis, financial metrics, competitive intelligence, and investment recommendation
- Works for **any US public company** — auto-ingests data on first query
- Report saved as timestamped Markdown file

---

## SLIDE 4: Key Features

- **Fully autonomous**: Zero manual research required
- **Multi-source data**: SEC filings (backward-looking) + live news (forward-looking)
- **4 specialized AI agents**: Risk, Financial, Competitive, Synthesis
- **Auto-ingestion**: First query for any company triggers automatic data scraping and embedding
- **Company-filtered search**: Prevents cross-company data contamination
- **Grounded answers**: LLM answers strictly from provided SEC filing context — no hallucination
- **Persistent storage**: ChromaDB survives between sessions — no re-ingestion needed
- **Full observability**: Every LLM call traced via LangSmith
- **Report export**: Saved as Markdown with timestamp

---

## SLIDE 5: Architecture Overview

```
USER INPUT: "Alphabet"
       │
       ▼
┌──────────────────────────┐
│    DATA INGESTION        │
│  SEC EDGAR API → 10-K    │
│  Tavily API → News       │
└─────────┬────────────────┘
          │
          ▼
┌──────────────────────────┐
│    VECTOR STORE          │
│  Clean → Chunk → Embed   │
│  ChromaDB (persistent)   │
└─────────┬────────────────┘
          │
          ▼
┌──────────────────────────┐
│    RAG CHAIN             │
│  Query → Retrieve → LLM  │
│  Company-filtered search │
└─────────┬────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────┐
│              LANGGRAPH AGENT PIPELINE              │
│  Risk → Financial → Competitive → Synthesis → END │
│          (shared TypedDict state)                  │
└─────────┬──────────────────────────────────────────┘
          │
          ▼
      📋 FINAL REPORT (saved to reports/)
```

---

## SLIDE 6: Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.14 |
| LLM | Llama 3.1 8B (local via Ollama) |
| Orchestration | LangChain + LangGraph |
| Embeddings | nomic-embed-text (local via Ollama) |
| Vector DB | ChromaDB (persistent, cosine similarity) |
| Data Source | SEC EDGAR API (official filings) |
| News Source | Tavily API (AI-optimized search) |
| HTML Parsing | BeautifulSoup |
| Observability | LangSmith (tracing + evaluation) |
| Config | python-dotenv (.env file) |

---

## SLIDE 7: Workflow — How Data Moves Through the System

**Step 1:** User enters company name → SEC EDGAR resolves to CIK + ticker

**Step 2:** `ensure_company_data()` checks ChromaDB → auto-ingests if missing:
- Download 10-K HTML → parse with BeautifulSoup → strip XBRL tags
- Chunk into 1000-char segments (200-char overlap)
- Embed with nomic-embed-text → store in ChromaDB with metadata

**Step 3:** Tavily API fetches 5 recent news articles → chunk → embed → store

**Step 4:** LangGraph runs 4 agents sequentially on shared state:
- Risk Agent: 3 RAG queries (risk factors, legal, operational)
- Financial Agent: 3 RAG queries (revenue, margins, debt)
- Competitive Agent: 3 RAG queries (market position, competitors, strategy)
- Synthesis Agent: combines all analyses into final report

**Step 5:** Report printed + saved to `reports/{TICKER}_{timestamp}.md`

---

## SLIDE 8: Key Challenges & Solutions

| Challenge | Solution |
|---|---|
| Cross-company data contamination | Added `company_name` metadata filter on every ChromaDB query |
| System only worked for pre-loaded companies | Built `ensure_company_data()` auto-ingestion guard |
| LLM hallucinating beyond filing data | System prompt constrains answers to provided context only |
| Agents each asked for company name separately | Moved input to single entry point; state flows through graph |
| News article ID collisions in ChromaDB | Added article-level index offset (`article_idx * 100 + chunk_idx`) |
| SEC filing text too long for LLM context | Chunking with overlap (1000 chars, 200 overlap) + top-k retrieval |
| Insufficient data retrieval (5 chunks) | Increased to 10 chunks per query for better coverage |

---

## SLIDE 9: Results & Impact

- **Analyzed 6+ companies** successfully: Alphabet, Apple, Microsoft, Tesla, Walmart, Q2 Holdings
- **4,000+ document chunks** embedded in ChromaDB across multiple companies
- **9 RAG queries + 1 synthesis** per company (~10 LLM calls per report)
- **Reports include**: Executive Summary, Key Findings, Risk Assessment, Financial Health, Competitive Position, Confidence Score
- **8 out of 9 answers** in initial testing were rated as strong/accurate (grounded in real SEC data)
- **Full pipeline runtime**: ~8-10 minutes per company (local inference)
- **Reports cite specific filing sections**: Item 1A Risk Factors, Part II Item 7A, Form 10-K page references

---

## SLIDE 10: Future Scope

- **Parallel agent execution** — cut runtime by 60% by running 3 agents concurrently
- **Multi-year trend analysis** — ingest 3-5 years of filings, detect revenue/risk trends
- **Hybrid search** — combine vector search with keyword search (BM25) for financial tables
- **Web UI** — Streamlit/Next.js dashboard for interactive browsing
- **Company comparison mode** — side-by-side analysis for investment decisions
- **Scheduled data refresh** — APScheduler for automatic periodic re-ingestion
- **PDF export** — formatted reports with charts and visualizations
- **Production LLM** — upgrade to GPT-4 / Claude for higher quality synthesis

---

## SLIDE 11: Summary

**What I built:** An end-to-end AI system that automates financial due diligence

**How it works:** SEC filings + news → vector DB → 4 AI agents → professional report

**Key technical decisions:**
- Local LLM (Ollama) for cost and privacy
- ChromaDB with company-filtered cosine similarity search
- LangGraph for stateful, graph-based agent orchestration
- Auto-ingestion pattern for zero-setup company analysis

**What it demonstrates:** RAG, multi-agent systems, vector databases, API integration, LLM orchestration, production-grade error handling

**Bottom line:** Type a company name → get a due diligence report. No manual research required.
