# 🎤 Interview Preparation — Financial Due Diligence Agent

---

## 1. "Tell Me About This Project" (60–90 seconds)

> "I built an autonomous financial due diligence agent that analyzes any US public company using their actual SEC filings. You type a company name — say, 'Alphabet' — and the system automatically scrapes their 10-K filings from SEC EDGAR, fetches recent news via the Tavily API, chunks and embeds all that text into a local ChromaDB vector database, and then runs four specialized AI agents — one for risk analysis, one for financial metrics, one for competitive intelligence, and a synthesis agent that combines everything into a final report.
>
> The agents are orchestrated using LangGraph as a directed graph, sharing state through a TypedDict whiteboard pattern. Each agent performs company-filtered RAG queries against the vector store using a local Llama 3.1 model running through Ollama. The whole pipeline is traced via LangSmith for debugging and evaluation.
>
> What makes it interesting is the auto-ingestion pattern — if a company doesn't exist in the database yet, the system detects that and automatically scrapes, processes, and embeds their filings before answering. So it works for any public company out of the box, not just pre-loaded ones."

---

## 2. Technical Architecture Questions

### Q: Walk me through the architecture. How does data flow from input to output?

**A:** "The architecture has five distinct layers. First, the **data ingestion layer** — `sec_scraper.py` hits SEC EDGAR's API to resolve a company name to its CIK number, fetches filing metadata, and downloads the actual 10-K HTML. `news_scraper.py` queries the Tavily API for recent financial news.

Second, the **vector store layer** — `document_processor.py` cleans the raw text by stripping XBRL tags and normalizing whitespace, then chunks it into 1000-character segments with 200-character overlap to prevent information loss at boundaries. `chroma_store.py` embeds these chunks using the `nomic-embed-text` model and stores them in a persistent ChromaDB collection with cosine similarity.

Third, the **chains layer** — `retrieval_chain.py` is the RAG pipeline. It queries ChromaDB with a company-name filter, retrieves the top-k most relevant chunks, stuffs them into a prompt, and sends that to Llama 3.1 for a grounded answer. It also has `ensure_company_data()` which checks if data exists before querying and auto-ingests if not.

Fourth, the **agents layer** — four LangGraph node functions. Risk, Financial, and Competitive agents each ask 3 targeted questions through the RAG chain. The Synthesis agent reads all three outputs and uses the LLM to produce a unified report.

Fifth, the **graph layer** — `workflow.py` uses LangGraph's `StateGraph` to wire the agents sequentially: Risk → Financial → Competitive → Synthesis → END. All agents share a `TypedDict` state dictionary. The graph is compiled into an executable app and invoked with the initial state."

---

### Q: Why did you use a sequential agent graph instead of running agents in parallel?

**A:** "I chose sequential execution because all three analysis agents call `ensure_company_data()` at the start, which checks and potentially writes to ChromaDB. Running them in parallel could cause race conditions — two agents might both detect the data is missing and try to ingest simultaneously. Sequential also made debugging easier since I could trace issues to a specific agent's turn.

That said, I'd refactor for parallel execution in production. I'd move `ensure_company_data()` to a separate ingestion node that runs first, then fan out the three analysis agents in parallel, and finally converge into the synthesis agent. LangGraph supports this natively with `add_edge` to multiple nodes."

---

### Q: How does the RAG pipeline prevent hallucination?

**A:** "Three mechanisms. First, the system prompt explicitly tells the LLM: 'Answer based ONLY on the following context from SEC filings. If the context doesn't contain enough information, say so.' So the LLM is instructed to refuse rather than hallucinate.

Second, company-filtered retrieval — every `ask_question()` call passes `company_name` which becomes a ChromaDB `where` filter: `{\"company\": company_name}`. This prevents cross-company contamination where asking about Tesla might return Apple's chunks because they're semantically similar.

Third, citation requirements — the prompt instructs the LLM to cite which filing section the information comes from (e.g., 'Item 1A Risk Factors' or 'Part II Item 7A'). This makes it easy to verify answers against the source documents."

---

### Q: How does `ensure_company_data()` work? What's the auto-ingestion pattern?

**A:** "It's a guard function that runs before any agent queries. It does a `collection.get(where={\"company\": company_name}, limit=1)` — a metadata-only lookup, not a semantic search. If the result has zero IDs, the company doesn't exist in the database.

At that point, it triggers the full ingestion pipeline: `get_company_cik()` resolves the name to a CIK number, `get_filings()` fetches the most recent 10-K filing metadata from SEC EDGAR, `process_filing()` downloads the HTML, cleans it, chunks it, and `add_chunks_to_collection()` embeds and stores everything.

This means the system works for any of the ~10,000 public companies on SEC EDGAR without pre-loading. The first query for a new company takes longer — maybe 30-60 seconds for ingestion — but subsequent queries are instant."

---

### Q: How do you handle errors in the pipeline?

**A:** "I handle errors at multiple levels. In `main.py`, the news fetching is wrapped in a try-except — if Tavily is down or the API key is invalid, it prints a warning and continues with SEC filings only, since news is supplementary.

In `sec_scraper.py`, HTTP responses are checked for non-200 status codes. If SEC returns an error, the function returns `None` and the caller handles it gracefully — `get_company_cik()` returns `None`, `main.py` prints an error and exits.

In `fetch_and_store_news()`, there's an early return if no articles are found, preventing `ingest_news_to_chromadb()` from being called with an empty list. And `download_filing_text()` returns `None` on failure, which `process_filing()` checks before proceeding."

---

## 3. "Why X Instead of Y" — Technology Choice Questions

### Q: Why Ollama + Llama 3.1 instead of OpenAI's GPT-4?

**A:** "Three reasons. First, **cost** — during development I was making hundreds of LLM calls for testing. At $0.03 per 1K tokens with GPT-4, that would've been expensive. Ollama is completely free.

Second, **privacy** — SEC filings contain sensitive financial data. With Ollama, everything stays on my machine. No data leaves the network.

Third, **latency control** — local inference means no network variability. I can also easily swap models — if I want better quality, I can switch to Llama 3.1 70B by changing one string. In production, I'd likely use GPT-4 or Claude for higher quality output, but the architecture is model-agnostic."

---

### Q: Why ChromaDB instead of Pinecone or Weaviate?

**A:** "ChromaDB was the right choice for this stage of the project. It has a `PersistentClient` that stores data locally to disk — no cloud account, no API keys, no cost. For development and testing with ~4,000 document chunks, it performs well.

The tradeoff is scalability — ChromaDB loads the full index into memory, which won't work for millions of documents. For production with hundreds of companies and years of filings, I'd move to Pinecone for managed scaling or Weaviate for self-hosted with better filtering capabilities.

I also chose cosine similarity over Euclidean distance because it measures directional similarity between vectors, which is more appropriate for semantic comparison — two chunks about 'revenue growth' should match regardless of their vector magnitudes."

---

### Q: Why LangGraph instead of just calling agents in sequence with normal Python?

**A:** "I could have used a simple for-loop, but LangGraph gives me three things plain Python doesn't.

First, **shared state management** — the `TypedDict` whiteboard pattern means each agent reads from and writes to a structured, type-checked state. If I add a new agent, I just add a key to the TypedDict and a node to the graph.

Second, **built-in tracing** — LangGraph integrates with LangSmith, so every node execution, state transition, and LLM call is automatically traced. With plain Python, I'd have to add logging manually.

Third, **future flexibility** — right now it's a linear graph, but LangGraph supports conditional edges, parallel branches, and human-in-the-loop interrupts. If I wanted to add a 'should we do deeper analysis?' routing decision, it's just one conditional edge. With plain Python, that's a major refactor."

---

### Q: Why Tavily for news instead of building your own web scraper?

**A:** "Custom scrapers are fragile — news sites change their HTML structure regularly, use anti-bot measures, and require per-site parsing logic. Tavily is an AI-optimized search API that returns pre-cleaned content. It's one API call instead of maintaining scrapers for Reuters, Yahoo Finance, Bloomberg, etc.

The tradeoff is cost and dependency — Tavily's free tier has 1,000 searches/month, and if their API goes down, news ingestion fails. That's why I wrapped it in a try-except in `main.py` — the pipeline degrades gracefully to SEC-only analysis."

---

### Q: Why character-based chunking instead of LangChain's RecursiveCharacterTextSplitter?

**A:** "I implemented a manual sliding-window chunker — `chunk_text(text, chunk_size=1000, overlap=200)` — to deeply understand the mechanics. It's a simple while-loop that slices text and advances by `chunk_size - overlap` each iteration.

In production, I'd use `RecursiveCharacterTextSplitter` because it splits at natural boundaries (paragraphs, sentences, words) before falling back to character-level splits. My chunker can cut mid-sentence, which occasionally hurts retrieval quality. The overlap of 200 characters partially mitigates this by ensuring boundary content appears in both adjacent chunks."

---

## 4. Conceptual Questions

### Q: What is RAG and why is it better than fine-tuning for this use case?

**A:** "RAG — Retrieval-Augmented Generation — retrieves relevant documents at query time and stuffs them into the LLM prompt as context. Fine-tuning permanently alters the model's weights with training data.

For financial due diligence, RAG is clearly better for three reasons. First, **freshness** — SEC filings are updated quarterly. Fine-tuning would require retraining every quarter. RAG just needs new documents in the vector store. Second, **auditability** — with RAG, I can trace every answer back to the specific filing chunks that were retrieved. Fine-tuned models can't cite sources. Third, **cost** — fine-tuning Llama 3.1 would require significant compute. RAG works with the base model."

---

### Q: What are the different types of RAG architectures?

**A:** "There are three main types. **Naive RAG** is the basic pipeline: retrieve chunks → stuff into prompt → generate. That's what I use here. It works well but can struggle when the right information is spread across many chunks.

**Advanced RAG** adds pre-retrieval and post-retrieval optimizations: query rewriting, hypothetical document embeddings (HyDE), re-ranking retrieved chunks, and context compression. If I had more time, I'd add a re-ranking step using a cross-encoder to improve retrieval precision.

**Modular RAG** treats each component as a pluggable module — you can swap retrievers, add routing logic, chain multiple retrieval steps. My agent architecture is actually modular in spirit — each agent is an independent RAG pipeline with its own questions, and the synthesis agent combines their outputs."

---

### Q: How does a vector database store and search documents?

**A:** "The process has three phases. **Embedding** — each text chunk is converted to a high-dimensional vector (768 dimensions with nomic-embed-text) that captures semantic meaning. Similar concepts land near each other in vector space.

**Indexing** — ChromaDB uses an HNSW (Hierarchical Navigable Small World) index, which is a graph-based structure optimized for approximate nearest-neighbor search. It's not searching every vector — it navigates the graph to find candidates quickly.

**Querying** — the user's question is also embedded into the same vector space, and the index finds the k-nearest vectors using cosine similarity. The corresponding text chunks are returned as context. The key insight is that 'What are the company's risks?' and 'risk factors and uncertainties' map to nearby vectors even though they share few exact words."

---

### Q: What's the difference between cosine similarity and Euclidean distance for embeddings?

**A:** "Cosine similarity measures the angle between two vectors — if they point in the same direction, they're similar, regardless of magnitude. Euclidean distance measures the straight-line distance between points.

I chose cosine for this project because document chunks vary in length. A long chunk about revenue risks and a short chunk about revenue risks would have different vector magnitudes with Euclidean distance, even though they're semantically identical. Cosine similarity normalizes for magnitude, focusing purely on meaning."

---

## 5. Challenges Faced & How They Were Solved

### Q: What was the hardest bug you encountered?

**A:** "Cross-company data contamination. When I first built the RAG chain, `ask_question('What are Tesla's risks?')` was returning chunks from Apple's filings because they were semantically similar — both tech companies discuss similar risk categories.

The fix was adding a company-name metadata filter. Every chunk stored in ChromaDB carries a `company` metadata field. The `ask_question()` function passes `company_name` which creates a `where={\"company\": company_name}` filter on the ChromaDB query. This scopes every search to only that company's documents."

---

### Q: How did you handle the auto-ingestion challenge?

**A:** "Originally, the system only worked for companies that were pre-loaded into ChromaDB. Users had to manually run the scraper before querying. I created `ensure_company_data()` as a guard function — it checks ChromaDB for existing data and triggers the full ingestion pipeline if nothing's found. This made the system work for any public company on first query. The tradeoff is that the first query for a new company takes 30-60 seconds for ingestion, but every subsequent query is instant."

---

### Q: How did you handle the ID collision issue with news articles?

**A:** "The original `add_chunks_to_collection()` generated IDs using `{ticker}_{form_type}_{chunk_index}`. This worked for SEC filings but crashed for news articles — they don't have a `form_type` field. And even after fixing that, all news articles were getting the same ID (`AAPL_news_0`) because each produced one chunk with `chunk_index: 0`.

I fixed both issues: used `.get('form_type', .get('source', 'unknown'))` for flexible ID generation, and added an article-level index (`article_idx * 100 + chunk_idx`) so each article gets unique IDs."

---

## 6. Scalability, Testing & Future Improvements

### Q: How would you scale this for production?

**A:** "Three main changes. First, swap ChromaDB for Pinecone or Weaviate — they handle millions of vectors with distributed indexing. Second, replace Ollama with an API-based LLM (GPT-4, Claude) behind a rate limiter for higher quality and throughput. Third, run the three analysis agents in parallel using LangGraph's native parallel execution to cut total time by 60%."

---

### Q: How would you add testing?

**A:** "I'd add three layers. Unit tests for individual functions — `clean_text()`, `chunk_text()`, `get_company_cik()` — using pytest with known inputs and expected outputs. Integration tests that verify the RAG pipeline returns relevant chunks for known queries. And evaluation tests using LangSmith datasets — store gold-standard Q&A pairs and measure answer quality over time."

---

### Q: What would you improve with more time?

**A:** "Five things:
1. **Parallel agent execution** — run Risk, Financial, Competitive agents concurrently
2. **Multi-year analysis** — ingest 3-5 years of 10-K filings to enable trend analysis
3. **Hybrid search** — combine vector search with keyword search (BM25) for better retrieval of specific financial numbers
4. **Web UI** — Streamlit dashboard for interactive report browsing and comparison
5. **Company comparison mode** — analyze two companies side-by-side for investment decisions"

---

## 7. Curveball / Edge-Case Questions

### Q: What happens if someone queries a private company that's not on SEC EDGAR?

**A:** "`get_company_cik()` searches SEC's master list and returns `None`. `main.py` catches this and prints 'Company not found in SEC EDGAR. Try the official name or ticker.' The system gracefully exits. For private companies, you'd need alternative data sources like Crunchbase or PitchBook."

---

### Q: What if the Ollama server isn't running?

**A:** "The first LLM call would fail with a connection error. Currently there's no explicit check for this — it would surface as an unhandled exception. I'd add a health check in `main.py` at startup: try to call `ChatOllama` with a simple prompt and catch the `ConnectionError` with a helpful message like 'Start Ollama with: ollama serve'."

---

### Q: Could your system be gamed by a company that uses unusual language in their filings to avoid risk keyword detection?

**A:** "That's the beauty of semantic search over keyword search. Even if a company avoids the word 'risk,' our embedding model captures the *meaning* of the text. Phrases like 'factors that may adversely affect our operations' would still be semantically close to 'risk factors.' However, very creative obfuscation could reduce retrieval accuracy. A re-ranking step or using multiple query phrasings would add robustness."

---

### Q: What's the context window limitation and how does it affect your system?

**A:** "Llama 3.1 8B has a 128K context window, but practical quality degrades with very long contexts. With `n_results=10` chunks of ~1000 characters each, I'm using about 10,000 characters (~2,500 tokens) of context per query — well within the sweet spot.

The tradeoff is coverage vs. quality. Too few chunks and you miss relevant information. Too many and the LLM gets confused with irrelevant noise. Ten chunks is a balanced default that works well for most queries."

---

### Q: If you had to rebuild this from scratch, what would you do differently?

**A:** "Honestly, two things. First, I'd use LangChain's `RecursiveCharacterTextSplitter` from the start instead of a manual chunker — it splits at natural language boundaries which improves retrieval quality. Second, I'd separate the ingestion pipeline from the query pipeline more cleanly — right now `ensure_company_data()` is in `retrieval_chain.py`, which mixes concerns. I'd create a dedicated `ingestion_service.py` that both `main.py` and the agents import."
