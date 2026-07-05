# 🏦 Autonomous Financial Due Diligence Agent

> Type a company name. Get a professional due diligence report — powered by SEC filings, real-time news, and a team of AI agents.

---

## Why This Project Exists

Investment banks and PE firms spend **200–400 hours per deal** manually reading SEC filings, cross-referencing financial data, and writing due diligence reports. Analysts wade through hundreds of pages of 10-K filings to extract risk factors, financial metrics, and competitive intelligence — often under extreme time pressure.

This project automates that entire workflow. A user enters a company name, and within minutes receives a structured, multi-dimensional due diligence report grounded entirely in official SEC filings and real-time news — with zero manual research required.

---

## What It Does

- **Accepts any US public company** by name or ticker symbol
- **Scrapes SEC EDGAR** for official 10-K, 10-Q, and 8-K filings
- **Fetches real-time news** via the Tavily API for forward-looking context
- **Embeds and stores** all documents in a local vector database (ChromaDB)
- **Runs 4 specialized AI agents** that analyze risk, financials, competitive position, and synthesize findings
- **Generates a professional report** with executive summary, key findings, confidence scores, and recommendations
- **Saves reports to disk** as timestamped Markdown files
- **Traces all LLM calls** via LangSmith for debugging and evaluation
- **Auto-ingests on first query** — if a company isn't in the database yet, it's automatically scraped, processed, and embedded

---

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          main.py (Entry Point)                      │
│         User Input → SEC Lookup → Data Ingestion → Agent Pipeline   │
└───────────────┬─────────────────────────────────────────────────────┘
                │
    ┌───────────┴───────────┐
    │   DATA INGESTION      │
    │                       │
    │  sec_scraper.py       │──→ SEC EDGAR API (10-K, 10-Q, 8-K)
    │  news_scraper.py      │──→ Tavily API (real-time news)
    └───────────┬───────────┘
                │ Raw text
                ▼
    ┌───────────────────────┐
    │   VECTOR STORE        │
    │                       │
    │  document_processor   │──→ Clean → Chunk (1000 chars, 200 overlap)
    │  chroma_store         │──→ Embed (nomic-embed-text) → Store (ChromaDB)
    └───────────┬───────────┘
                │ Embedded chunks with metadata
                ▼
    ┌───────────────────────┐
    │   RAG CHAIN           │
    │                       │
    │  retrieval_chain.py   │──→ Query ChromaDB → Retrieve top-k → LLM answers
    │  ensure_company_data  │──→ Auto-ingest if company not found
    └───────────┬───────────┘
                │ Grounded answers
                ▼
    ┌───────────────────────────────────────────────────────────────┐
    │                    LANGGRAPH WORKFLOW                         │
    │                                                               │
    │  ┌──────────┐   ┌────────────┐   ┌───────────────┐   ┌─────────────┐  │
    │  │  Risk    │──→│ Financial  │──→│ Competitive   │──→│  Synthesis  │──→ END
    │  │  Agent   │   │  Agent     │   │  Agent        │   │   Agent     │  │
    │  └──────────┘   └────────────┘   └───────────────┘   └─────────────┘  │
    │       ↑                                                               │
    │     START                                                             │
    │                                                                       │
    │  All agents share a TypedDict state (whiteboard pattern)              │
    └───────────────────────────────────┬───────────────────────────────────┘
                                        │
                                        ▼
                                  📋 Final Report
                            (saved to reports/{TICKER}_{timestamp}.md)
```

### Data Flow

1. **User enters** a company name (e.g., "Alphabet")
2. **SEC EDGAR lookup** resolves the name to CIK `0001652044` and ticker `GOOGL`
3. **`ensure_company_data()`** checks ChromaDB — if no data exists, it auto-ingests:
   - Downloads 10-K filing HTML from SEC EDGAR
   - Parses with BeautifulSoup, strips XBRL tags
   - Chunks into 1000-character overlapping segments
   - Embeds with `nomic-embed-text` via Ollama
   - Stores in ChromaDB with metadata (company, ticker, form_type, filing_date)
4. **Tavily API** fetches 5 recent news articles, chunks them (500 chars), and stores alongside filings
5. **LangGraph** runs the agent pipeline sequentially:
   - **Risk Agent**: 3 RAG queries about risk factors, legal risks, operational risks
   - **Financial Agent**: 3 RAG queries about revenue, margins, debt/liquidity
   - **Competitive Agent**: 3 RAG queries about market position, competitors, growth strategy
   - **Synthesis Agent**: Reads all 3 analyses, prompts LLM to produce unified report
6. **Final report** is printed and saved to `reports/GOOGL_20260704_202334.md`

---

## Tech Stack

| Technology | Role | Why This Choice |
|---|---|---|
| **Python 3.14** | Core language | Industry standard for ML/AI pipelines |
| **Ollama + Llama 3.1 8B** | Local LLM | Free, private, offline-capable. No API costs. Runs natively on Apple Silicon. |
| **LangChain** | Chain building (LCEL) | De facto standard for RAG pipelines. `prompt \| llm \| parser` syntax. |
| **LangGraph** | Agent orchestration | Stateful graph-based workflows. Agents share state via TypedDict. Supports complex routing patterns. |
| **ChromaDB (PersistentClient)** | Vector database | Free, local, persistent across sessions. Cosine similarity search with metadata filtering. |
| **nomic-embed-text** | Embedding model | Free, runs locally via Ollama. Good quality for document retrieval tasks. |
| **SEC EDGAR API** | Financial data source | Official, free, real-time access to all US public company filings. |
| **Tavily API** | News search | AI-optimized search engine. Returns pre-cleaned content. More reliable than custom scrapers. |
| **BeautifulSoup** | HTML parsing | Extracts clean text from SEC filing HTML. Handles malformed markup. |
| **LangSmith** | Observability | Traces every LLM call with prompts, responses, latency, token usage. |
| **python-dotenv** | Config management | Loads API keys from `.env` file. Keeps secrets out of code. |

---

## Project Structure

```
financial-due-diligence/
│
├── main.py                          ← Single entry point: runs full pipeline
├── test_setup.py                    ← Environment verification script
├── .env                             ← API keys (LangSmith, Tavily) — NOT committed
├── .gitignore                       ← Excludes venv, .env, chroma_db, __pycache__
├── requirements.txt                 ← All Python dependencies (pip freeze)
│

├── data_ingestion/                  ← LAYER 1: Data acquisition
│   ├── __init__.py
│   ├── sec_scraper.py              ←   SEC EDGAR: CIK lookup, filing fetch, HTML download
│   └── news_scraper.py             ←   Tavily API: news search, chunk, embed, store
│
├── vector_store/                    ← LAYER 2: Embedding & storage
│   ├── __init__.py
│   ├── document_processor.py       ←   Clean XBRL → chunk text → attach metadata
│   └── chroma_store.py             ←   ChromaDB: embed, store, query (cosine similarity)
│
├── chains/                          ← LAYER 3: RAG pipeline
│   ├── __init__.py
│   └── retrieval_chain.py          ←   Retrieve context → LLM answer → auto-ingest
│
├── agents/                          ← LAYER 4: Specialized AI agents
│   ├── __init__.py
│   ├── state.py                    ←   AgentState TypedDict (shared whiteboard)
│   ├── risk_agent.py               ←   Risk factors, legal, operational analysis
│   ├── financial_agent.py          ←   Revenue, margins, debt/liquidity analysis
│   ├── competitive_agent.py        ←   Market position, competitors, growth strategy
│   └── synthesis_agent.py          ←   Combines all analyses into final report
│
├── graph/                           ← LAYER 5: Orchestration
│   ├── __init__.py
│   └── workflow.py                 ←   LangGraph StateGraph: nodes, edges, compile
│
├── reports/                         ← Generated reports (timestamped .md files)
│   ├── GOOGL_20260704_202334.md
│   └── QTWO_20260701_201733.md
│
└── chroma_db/                       ← Persistent vector database (auto-created)
```

---

## Setup & Installation

### Prerequisites
- macOS with Apple Silicon (tested on M4) or Linux
- Python 3.12+
- [Ollama](https://ollama.ai/) installed

### Step-by-step

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/financial-due-diligence.git
cd financial-due-diligence

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Pull required Ollama models
ollama pull llama3.1:8b
ollama pull nomic-embed-text

# 5. Start Ollama server (in a separate terminal)
ollama serve

# 6. Set up environment variables
# Create a .env file with:
echo 'LANGCHAIN_TRACING_V2=true' > .env
echo 'LANGCHAIN_API_KEY=your_langsmith_key' >> .env
echo 'LANGCHAIN_PROJECT=financial-due-diligence' >> .env
echo 'TAVILY_API_KEY=your_tavily_key' >> .env

# 7. Verify setup
python test_setup.py
```

---

## Usage

### Full Pipeline (Recommended)
```bash
python main.py
# Enter company name: Alphabet
# → Scrapes SEC, fetches news, runs 4 agents, generates report
# → Report saved to reports/GOOGL_20260704_202334.md
```

### Individual Components
```bash
# Interactive RAG Q&A
python -m chains.retrieval_chain

# Test individual agents
python -m agents.risk_agent
python -m agents.financial_agent
python -m agents.competitive_agent

# Test news scraper
python -m data_ingestion.news_scraper

# Run agent pipeline without main.py wrapper
python -m graph.workflow
```

---

## Key Functions

| Function | File | Purpose |
|---|---|---|
| `get_company_cik(name)` | `sec_scraper.py` | Resolves company name/ticker to SEC CIK number |
| `get_filings(cik, types, count)` | `sec_scraper.py` | Fetches recent filings from SEC EDGAR submissions API |
| `download_filing_text(url)` | `sec_scraper.py` | Downloads and parses filing HTML with BeautifulSoup |
| `clean_text(raw)` | `document_processor.py` | Strips XBRL tags, normalizes whitespace |
| `chunk_text(text, size, overlap)` | `document_processor.py` | Splits text into overlapping chunks |
| `process_filing(filing, name, ticker)` | `document_processor.py` | Full pipeline: download → clean → chunk → metadata |
| `add_chunks_to_collection(coll, chunks)` | `chroma_store.py` | Embeds and stores chunks in ChromaDB |
| `query_collection(coll, query, n, where)` | `chroma_store.py` | Semantic search with optional metadata filter |
| `retrieve_context(question, company)` | `retrieval_chain.py` | Queries ChromaDB, joins top chunks as context string |
| `ask_question(question, company, n)` | `retrieval_chain.py` | Full RAG: retrieve → prompt → LLM → answer |
| `ensure_company_data(name)` | `retrieval_chain.py` | Auto-ingests from SEC if company not in ChromaDB |
| `search_company_news(name, max)` | `news_scraper.py` | Searches Tavily API for recent articles |
| `fetch_and_store_news(name, ticker)` | `news_scraper.py` | Searches news and ingests into ChromaDB |
| `build_workflow()` | `workflow.py` | Creates and compiles the LangGraph StateGraph |
| `risk_agent(state)` | `risk_agent.py` | 3 risk-focused RAG queries → structured report |
| `financial_agent(state)` | `financial_agent.py` | 3 finance-focused RAG queries → structured report |
| `competitive_agent(state)` | `competitive_agent.py` | 3 competition-focused RAG queries → structured report |
| `synthesis_agent(state)` | `synthesis_agent.py` | Combines all 3 analyses into final unified report |

---

## Known Limitations & Future Improvements

### Current Limitations
- **Sequential execution**: Agents run one after another (~8-10 minutes total). LangGraph supports parallel execution but it's not implemented yet.
- **Chunk-based retrieval**: Semantic search with 10 chunks may miss data in specific financial tables. Larger retrieval windows or hybrid search would improve accuracy.
- **Single filing depth**: Currently ingests only the most recent 10-K. Ingesting multiple years would enable trend analysis.
- **No authentication**: The system is a CLI tool with no user authentication or multi-tenancy.
- **News volume**: Tavily's free tier allows 1,000 searches/month. Production use would need a paid plan.

### Future Improvements
- **Parallel agent execution**: Run Risk, Financial, and Competitive agents concurrently
- **Scheduled data refresh**: APScheduler to periodically re-ingest filings and news
- **Web UI**: Streamlit or Next.js frontend for interactive report browsing
- **Comparison mode**: Analyze two companies side-by-side
- **Citation linking**: Hyperlink specific claims in the report back to source filing sections
- **PDF export**: Generate formatted PDF reports from the Markdown output
- **Model upgrade**: Support for larger models (Llama 3.1 70B, GPT-4) for higher quality analysis

---

## Sample Output

Reports are saved to `reports/{TICKER}_{timestamp}.md`. The final synthesized report includes:

- **Executive Summary** — High-level overview of the company
- **Key Findings (Top 5)** — Most important discoveries across all analyses
- **Risk Assessment** — Strategic, regulatory, operational, cybersecurity risks with severity
- **Financial Health** — Revenue, margins, debt, cash position with multi-year trends
- **Competitive Position** — Market standing, competitors, advantages/disadvantages
- **Overall Recommendation** — Investment thesis with confidence score (High/Medium/Low)

Successfully generated reports for: Alphabet (GOOGL), Q2 Holdings (QTWO), Microsoft (MSFT), Walmart (WMT), Apple (AAPL), Tesla (TSLA), and others.

---

## License

This project is for educational and research purposes.