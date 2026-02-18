# Research Paper Analyzer

> **Language:** English | [Deutsch](README.de.md)

**AI-powered analysis of scientific research papers using 8 specialized agents.**

Upload any research paper PDF and receive a comprehensive, multi-dimensional analysis in minutes — covering methodology, writing quality, data visualizations, citations, plagiarism risk, journal recommendations, and funding opportunities.

**[Try the Live Demo](https://research-paper-analyzer-2026.streamlit.app/)** — 3 pre-analyzed papers available instantly, no account needed.

---

## What It Does

Most paper review tools focus on a single dimension. This analyzer deploys **8 independent AI agents**, each specialized in a different aspect of academic paper evaluation. They run in parallel and return structured, actionable feedback.

| Agent | What It Evaluates | Key Output |
|-------|-------------------|------------|
| **Results Synthesizer** | Key findings, effect sizes, statistical significance | Evidence strength rating, p-values, confidence intervals |
| **Writing Coach** | Academic writing quality per section | Score (1-5), passive voice %, sentence length, style guide references |
| **Methodology Critic** | Study design, sample size, bias, reproducibility | Quality score (1-5), identified biases, critical issues |
| **DataViz Critic** | Figures against Tufte/Cleveland/Few best practices | Per-figure scores, colorblind accessibility, chart junk detection |
| **Citation Hunter** | Related literature via Semantic Scholar | Supporting & conflicting papers, research gaps |
| **Plagiarism Detector** | Missing citations, suspicious paraphrasing | Risk score (0-100), flagged sections with severity |
| **Journal Recommender** | Target journals via OpenAlex metrics | 5+5 ranked journals with impact factor, h-index, APC, acceptance likelihood |
| **Funding Advisor** | Funding sources from similar funded research | Ranked funders with programs, typical amounts, eligibility, application tips |

### Supported Paper Types

- Original Research
- Review Articles / Literature Reviews
- Meta-Analyses
- Case Studies

---

## Architecture

```
PDF Upload
    |
    v
Text Extraction (pypdf) ──> Section Detection (LLM) ──> Paper Type Classification
    |
    v
 [PARALLEL EXECUTION - ThreadPoolExecutor]
 |        |         |        |        |         |         |
 v        v         v        v        v         v         v
Results  Writing  Methods  DataViz  Citations  Plagiarism  Funding
         |                                       |
         v                                       v
    (6 LLM calls,               (PyMuPDF extracts figures,
     Python regex                GPT-4o Vision analyzes
     + LLM hybrid)              up to 5 charts)
                     |
                     v
              Journal Recommender
         (runs after Methods + Results
          for better recommendations)
                     |
                     v
           Aggregate ──> Dashboard (9 tabs)
                    ──> JSON Export
                    ──> Markdown Report
```

**Key design decisions:**
- **Hybrid Python + LLM approach** — Python computes objective metrics (passive voice ratio, sentence length, hedge word count), LLM provides qualitative interpretation
- **LLM-based section detection** — Not regex-based, because academic papers vary widely across disciplines
- **Vision-based figure analysis** — GPT-4o Vision evaluates actual chart visuals, not just text descriptions
- **Paper-type aware** — Review papers get different plagiarism criteria (paraphrasing is expected), methodology is scored differently
- **Cross-section context** — Methodology agent reads Methods + Abstract + Results together for deeper analysis

---

## Demo Mode

Three pre-analyzed papers are included for instant exploration without Azure credentials:

| Paper | Type | Domain |
|-------|------|--------|
| Hospital Variation in THR Outcomes (n=583) | Original Research | Healthcare / Orthopedics |
| Pharmacological Advances in HIV Treatment | Review Article | Pharmacology / Infectious Disease |
| ML Framework for Stock Market Prediction | Original Research | Quantitative Finance / AI |

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Streamlit |
| LLM | Azure OpenAI (GPT-4o) |
| PDF Text | pypdf |
| PDF Images | PyMuPDF (fitz) |
| Citation Search | Semantic Scholar API (free) |
| Journal & Funding Data | OpenAlex API (free) |
| Image Processing | Pillow |
| Parallelization | concurrent.futures.ThreadPoolExecutor |

---

## Cost Per Analysis

Running all 8 agents on a typical 12-page paper:

| Agent | Cost | Time |
|-------|------|------|
| Results Synthesizer | ~$0.01 | ~5s |
| Writing Coach | ~$0.03 | ~30s |
| Methodology Critic | ~$0.02 | ~5s |
| DataViz Critic | ~$0.05-0.15 | ~60-120s |
| Citation Hunter | ~$0.02 | ~10s |
| Plagiarism Detector | ~$0.03 | ~5s |
| Journal Recommender | ~$0.04 | ~60-120s |
| Funding Advisor | ~$0.04 | ~60-120s |
| **Total** | **~$0.24-0.34** | **~3-5 min** |

Semantic Scholar and OpenAlex APIs are free. With parallel execution, total wall-clock time is determined by the slowest agent (~2-3 minutes).

---

## Local Setup

### Prerequisites

- Python 3.11+
- Azure OpenAI resource with a GPT-4o deployment

### Installation

```bash
git clone https://github.com/leelesemann-sys/research-paper-analyzer.git
cd research-paper-analyzer
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### Configuration

Copy `.env.example` to `.env` and fill in your Azure OpenAI credentials:

```
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

### Run

```bash
streamlit run Paper_Analyzer.py
```

The demo mode works without Azure credentials — you can explore 3 pre-analyzed papers immediately.

---

## Project Structure

```
research-paper-analyzer/
|-- Paper_Analyzer.py          # Streamlit frontend (main app)
|-- workflow.py                # Orchestrator: PDF processing, section detection, agent coordination
|-- agents/
|   |-- results.py             # Agent 1: Results Synthesizer
|   |-- writing.py             # Agent 2: Writing Quality Coach
|   |-- methodology.py         # Agent 3: Methodology Critic
|   |-- visualization.py       # Agent 4: DataViz Critic (Vision API)
|   |-- citations.py           # Agent 5: Citation Hunter (Semantic Scholar)
|   |-- plagiarism.py          # Agent 6: Plagiarism Detector
|   |-- journals.py            # Agent 7: Journal Recommender (OpenAlex)
|   |-- funding.py             # Agent 8: Funding Advisor (OpenAlex)
|-- pages/
|   |-- 1_How_It_Works.py      # Architecture & agent documentation page
|-- demo_data/                 # Pre-computed demo analyses (3 papers)
|-- requirements.txt
|-- .env.example
```

---

## License

This project is for portfolio and educational purposes.

---

Built with Azure OpenAI, Streamlit, Semantic Scholar, and OpenAlex.
