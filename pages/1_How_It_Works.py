import streamlit as st

st.set_page_config(
    page_title="How It Works - Paper Analyzer",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════
# CSS — Blue/Indigo theme to distinguish from main green app
# ═══════════════════════════════════════════════════════════════
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #e8eaf6 0%, #e3f2fd 50%, #ede7f6 100%);
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a237e 0%, #283593 40%, #3949ab 100%);
    }
    section[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p {
        color: #c5cae9 !important;
    }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
        color: #ffffff !important;
    }
    [data-testid="stSidebarNav"] {
        background: white;
        border-radius: 12px;
        padding: 0.8rem 0.5rem;
        margin: 0.5rem 0.8rem 1rem 0.8rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    [data-testid="stSidebarNav"] a {
        color: #1a237e !important;
        font-size: 1.3rem !important;
        font-weight: 700 !important;
        padding: 0.6rem 1rem !important;
        border-radius: 8px;
        transition: background 0.2s ease;
    }
    [data-testid="stSidebarNav"] a:hover {
        background: #e8eaf6 !important;
    }
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: #e8eaf6 !important;
        color: #1a237e !important;
    }
    [data-testid="stSidebarNav"] a span {
        color: #1a237e !important;
        font-size: 1.3rem !important;
        font-weight: 700 !important;
    }
    .how-header {
        background: linear-gradient(90deg, #283593, #3f51b5, #5c6bc0);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px rgba(40, 53, 147, 0.3);
    }
    .how-header h1 { color: white !important; font-size: 2.2rem !important; margin-bottom: 0.3rem !important; }
    .how-header p { color: #c5cae9 !important; font-size: 1.1rem !important; margin: 0 !important; }

    .tech-badge {
        background: #e8eaf6; color: #283593;
        padding: 0.25rem 0.7rem; border-radius: 20px;
        font-weight: 600; font-size: 0.8rem;
        display: inline-block; margin: 0.15rem 0.2rem;
    }
    .tech-badge.api { background: #e3f2fd; color: #1565c0; }
    .tech-badge.llm { background: #ede7f6; color: #4527a0; }
    .tech-badge.python { background: #e8f5e9; color: #2e7d32; }

    .pipeline-step {
        background: #f5f5f5; border-radius: 8px;
        padding: 0.6rem 1rem; margin: 0.3rem 0;
        border-left: 3px solid #5c6bc0; font-size: 0.9rem;
    }
    .arch-grid {
        display: grid;
        grid-template-columns: 2fr 1fr;
        gap: 1.5rem;
        margin-bottom: 1rem;
    }
    .arch-box {
        background: white; border-radius: 14px;
        padding: 1.5rem 2rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
        border-top: 3px solid #3f51b5;
        box-sizing: border-box;
    }

    /* Tables — white background for readability */
    .stMarkdown table {
        background: white;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    .stMarkdown th {
        background: #e8eaf6 !important;
    }

    /* Section headers */
    .section-head {
        color: #283593; font-size: 1.15rem; font-weight: 700;
        margin-top: 1.8rem; margin-bottom: 0.6rem;
        padding-bottom: 0.4rem;
        border-bottom: 2px solid #c5cae9;
    }

    /* Intelligence items */
    .intel-item {
        background: linear-gradient(135deg, #e3f2fd, #e8eaf6);
        border-left: 3px solid #1565c0;
        padding: 0.55rem 0.9rem; margin: 0.3rem 0;
        border-radius: 0 6px 6px 0; font-size: 0.9rem;
    }

    /* Challenge items */
    .challenge-item {
        background: linear-gradient(135deg, #fff3e0, #fff8e1);
        border-left: 3px solid #ef6c00;
        padding: 0.55rem 0.9rem; margin: 0.3rem 0;
        border-radius: 0 6px 6px 0; font-size: 0.9rem;
    }

    /* Economics cards */
    .econ-card {
        background: white; border-radius: 12px;
        padding: 1.1rem 1rem; text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border-top: 3px solid #43a047;
        min-height: 120px;
        display: flex; flex-direction: column; justify-content: center;
    }
    .econ-value { font-size: 1.7rem; font-weight: 700; color: #2e7d32; }
    .econ-label { font-size: 0.82rem; color: #555; margin-top: 0.25rem; }
    .econ-detail { font-size: 0.72rem; color: #999; margin-top: 0.3rem; }

    /* Radio navigation — base style */
    section[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"] {
        color: #e8eaf6 !important; font-size: 0.95rem !important;
        padding: 0.4rem 0.6rem !important;
        border-radius: 8px;
        transition: background 0.2s ease;
        border-left: 3px solid transparent;
    }
    section[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p {
        color: #c5cae9 !important;
    }
    /* Radio navigation — hover */
    section[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"]:hover {
        background: rgba(255, 255, 255, 0.08) !important;
    }
    /* Radio navigation — active/selected item */
    section[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"]:has(div[aria-checked="true"]) {
        background: rgba(255, 255, 255, 0.15) !important;
        border-left: 3px solid #90caf9 !important;
    }
    section[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"]:has(div[aria-checked="true"]) p {
        color: #ffffff !important;
        font-weight: 700 !important;
    }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# Navigation
# ═══════════════════════════════════════════════════════════════
AGENT_NAV = [
    "🏗️ Architecture Overview",
    "📊 Results Synthesizer",
    "✍️ Writing Coach",
    "🔬 Methodology Critic",
    "📈 DataViz Critic",
    "🔗 Citation Hunter",
    "🚨 Plagiarism Detector",
    "📚 Journal Recommender",
    "💰 Funding Advisor",
]

with st.sidebar:
    st.markdown("### Navigate")
    selected_agent = st.radio("Navigate", AGENT_NAV, label_visibility="collapsed")
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; opacity: 0.7; font-size: 0.85rem;">
        Paper Analyzer Documentation<br>
        8 AI Agents Explained
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# Header
# ═══════════════════════════════════════════════════════════════
st.markdown("""
<div class="how-header">
    <h1>📖 How It Works</h1>
    <p>Understand the architecture and methodology behind each of the 8 AI agents</p>
</div>
""", unsafe_allow_html=True)

st.markdown(f"## {selected_agent}")


# ═══════════════════════════════════════════════════════════════
# Agent Data — all 8 agents with 6 standardized sections
# ═══════════════════════════════════════════════════════════════

AGENT_DATA = {

    # ----------------------------------------------------------
    # Agent 1: Results Synthesizer
    # ----------------------------------------------------------
    "results": {
        "icon": "📊",
        "title": "Results Synthesizer",
        "what_it_does": """
Extracts and synthesizes the key findings from the **Results** section.

The agent identifies:
- **Primary outcome** with statistical significance and p-values
- **Effect sizes** with interpretation (small / medium / large) using Cohen's d, odds ratios, etc.
- **Secondary outcomes** and subgroup analyses
- **Confidence intervals** where reported
- **Clinical vs. statistical significance** distinction
""",
        "how_it_works": [
            ("Input", "Results section text"),
            ("Processing", "Single LLM call with structured JSON output"),
            ("Output", "Findings table, evidence strength, limitations"),
        ],
        "intelligence": [
            "<b>Cohen's Effect Size Benchmarks</b> &mdash; small (0.2), medium (0.5), large (0.8) per established convention (Cohen, 1988)",
            "<b>Clinical vs. Statistical Significance</b> &mdash; explicitly distinguishes p-value significance from real-world clinical impact",
            "<b>Confidence Interval Interpretation</b> &mdash; evaluates precision of estimates, not just point values",
            "<b>Statistical Test Recognition</b> &mdash; correctly interprets t-tests, chi-square, ANOVA, regression and their reporting formats",
            "<b>Evidence Strength Hierarchy</b> &mdash; weak / moderate / strong classification aligned with GRADE framework principles",
        ],
        "metrics": [
            ("Strength of Evidence", "weak / moderate / strong", "Standard in Cochrane Systematic Reviews &amp; GRADE Framework"),
            ("Primary Outcome + p-value", "Extracted text + number", "Core of every results section per CONSORT guidelines"),
            ("Effect Sizes", "Cohen's d / OR / RR + interpretation", "Required by APA 7th Edition &amp; most journals since 2000s"),
            ("Key Findings with Statistics", "List with CI, p-values", "Standard evidence extraction methodology"),
            ("Limitations Noted", "List", "Best practice: identify what authors acknowledge"),
        ],
        "challenges": [
            ("Statistical value extraction", "p-values, confidence intervals, and effect sizes must be correctly parsed from unstructured narrative text &mdash; no dedicated NER pipeline, relies on LLM precision"),
            ("Varied reporting formats", "Papers report statistics in many formats: p&lt;0.001, p=.003, F(2,147)=5.84, &chi;&sup2;=19.44 &mdash; agent must handle all"),
        ],
        "poc_vs_prod": [
            ("Single GPT-4.1 call", "Multi-model consensus (GPT + Claude cross-validation)"),
            ("LLM extracts statistics from text", "Dedicated NER/NLP pipeline (spaCy) for structured extraction"),
            ("No validation of extracted numbers", "Cross-check against tables and figures in the paper"),
            ("No GRADE assessment", "Full GRADE framework integration (Cochrane Risk-of-Bias)"),
        ],
        "economics": {
            "cost_per_paper": "~$0.01",
            "cost_details": "1 LLM call &bull; ~3K input + ~2K output tokens",
            "human_time": "1-2 hours",
            "human_desc": "for thorough results extraction and synthesis",
            "agent_time": "~5 sec",
        },
    },

    # ----------------------------------------------------------
    # Agent 2: Writing Quality Coach
    # ----------------------------------------------------------
    "writing": {
        "icon": "✍️",
        "title": "Writing Quality Coach",
        "what_it_does": """
Evaluates academic writing quality using a **hybrid approach**: quantitative Python-based text metrics combined with LLM-powered qualitative analysis.

Each of the 6 paper sections is evaluated against **section-specific standards**:

| Section | Key Standards |
|---------|--------------|
| Abstract | Concise, self-explanatory, IMRAD structure, no citations |
| Introduction | Funnel structure (broad → narrow), clear research gap |
| Methods | Precise, reproducible, passive voice acceptable |
| Results | Objective, no interpretation, statistics present |
| Discussion | Interpretation, honest limitations, literature comparison |
| Conclusion | Concise, implications, future work |
""",
        "how_it_works": [
            ("Step 1", "Python computes quantitative metrics per section (no LLM needed)"),
            ("Step 2", "LLM evaluates each section individually with metrics as context"),
            ("Step 3", "LLM synthesizes cross-section patterns into overall assessment"),
        ],
        "intelligence": [
            "<b>APA 7th Edition</b> &mdash; Section 4.13: prefer active voice for clarity and directness",
            "<b>Strunk &amp; White</b> &mdash; <i>The Elements of Style</i>: omit needless words, use active constructions",
            "<b>Schimel &ldquo;Writing Science&rdquo;</b> &mdash; one clear point per paragraph, logical story arc",
            "<b>Sword &ldquo;Stylish Academic Writing&rdquo;</b> &mdash; balance formality with readability",
            "<b>Day &amp; Gastel</b> &mdash; <i>How to Write and Publish a Scientific Paper</i>: section-specific conventions",
            "<b>Sentence Length Benchmarks</b> &mdash; 15-25 words ideal for academic text (empirically validated)",
            "<b>Passive Voice Thresholds</b> &mdash; &lt;25% good, 25-35% acceptable, &gt;35% excessive per APA guidelines",
            "<b>Type-Token Ratio</b> &mdash; &gt;0.40 indicates varied vocabulary (lexical diversity measure)",
            "<b>6 Section-Specific Evaluation Catalogs</b> &mdash; each section has its own detailed standards checklist",
            "<b>Curated Word Lists</b> &mdash; 19 hedge words, 17 filler phrases, 20 transition words compiled from style guides",
        ],
        "metrics": [
            ("6 Sub-Scores per Section", "Clarity, Conciseness, Tone, Structure, Precision, Section-Specific (each 1-5)", "Standard dimensions in academic writing assessment per APA/MLA"),
            ("Overall Writing Score", "1-5", "Aggregated across all sections"),
            ("Readability Level", "basic academic / advanced / expert only / mixed", "Target audience assessment"),
            ("Avg. Sentence Length", "words per sentence", "Empirically: 15-25 words = optimal readability"),
            ("Passive Voice Ratio", "percentage", "APA 7th recommends active voice for clarity"),
            ("Hedge / Filler Word Counts", "count", "Indicators for unclear or imprecise writing"),
            ("Problematic Sentences", "up to 5 per section with rewrites", "Concrete, actionable feedback &mdash; not just abstract scores"),
        ],
        "challenges": [
            ("Passive voice false positives", "&ldquo;was associated&rdquo; is correct in Methods &mdash; agent has section-specific tolerance built in so Methods sections aren&rsquo;t penalized for standard scientific passive"),
            ("Review papers without Methods", "Section is gracefully skipped instead of generating false low scores"),
            ("Hedge words in Discussion", "Hedging is expected and appropriate there &mdash; different thresholds applied per section"),
            ("Abbreviation handling in sentence splitting", "&ldquo;et al.&rdquo;, &ldquo;Fig.&rdquo;, &ldquo;e.g.&rdquo; would break naive sentence splitting &mdash; regex replacement preserves these"),
            ("Multi-word filler detection", "Phrases like &ldquo;it is worth noting that&rdquo; must be matched as units, not individual words"),
            ("Very short sections (&lt;50 chars)", "Graceful skip with note instead of LLM hallucination on minimal input"),
            ("Long sections exceeding token limits", "Truncation to 8,000 chars per section prevents API errors while preserving analysis quality"),
        ],
        "poc_vs_prod": [
            ("Python regex for quantitative metrics", "spaCy / NLTK NLP pipeline with POS tagging"),
            ("GPT-4.1 for qualitative analysis", "Claude Opus 4.6 (more nuanced, higher cost)"),
            ("Custom curated word lists", "Grammarly API + LanguageTool API"),
            ("No grammar checking", "Full grammar, spelling &amp; style checking"),
            ("6 scoring dimensions per section", "Genre-specific trained models (e.g., SciWriter)"),
        ],
        "economics": {
            "cost_per_paper": "~$0.03",
            "cost_details": "7 LLM calls (6 sections + 1 synthesis) &bull; Python metrics = $0",
            "human_time": "2-3 hours",
            "human_desc": "for comprehensive writing quality assessment",
            "agent_time": "~30 sec",
        },
    },

    # ----------------------------------------------------------
    # Agent 3: Methodology Critic
    # ----------------------------------------------------------
    "methodology": {
        "icon": "🔬",
        "title": "Methodology Critic",
        "what_it_does": """
Evaluates the research methodology by analyzing the **Methods** section, supplemented with context from the **Abstract** and **Results**.

The agent assesses five core dimensions:
1. **Sample Size** — participant counts, site numbers, group sizes (including numbers written as words)
2. **Study Design** — classifies type (RCT, cohort, case-control, etc.) and rates quality
3. **Statistical Methods** — appropriateness for data type, common mistakes
4. **Potential Biases** — selection bias, measurement bias, confounding
5. **Reproducibility** — can another researcher replicate this study?
""",
        "how_it_works": [
            ("Input", "Methods + Abstract + Results sections (cross-section context)"),
            ("Processing", "Single LLM call with structured JSON output, temperature 0.3"),
            ("Output", "Quality scores, bias list, strengths &amp; critical issues"),
        ],
        "intelligence": [
            "<b>Study Design Hierarchy</b> &mdash; RCT &gt; prospective cohort &gt; case-control &gt; cross-sectional &gt; case series (evidence pyramid)",
            "<b>Power Calculation Standards</b> &mdash; 80% power, alpha 0.05 as benchmark; flags when missing",
            "<b>Bias Framework</b> &mdash; systematic assessment of selection bias, measurement bias, and confounding variables",
            "<b>Reproducibility Criteria</b> &mdash; evaluates whether methods are described precisely enough for replication",
            "<b>Statistical Method Appropriateness</b> &mdash; knows which tests match which data types (e.g., t-test for continuous, chi-square for categorical)",
            "<b>Number-Word Conversion</b> &mdash; &ldquo;ten hospitals&rdquo; &rarr; n=10, &ldquo;twenty-three participants&rdquo; &rarr; n=23",
        ],
        "metrics": [
            ("Overall Quality", "1-5", "Aligned with CONSORT / STROBE assessment standards"),
            ("Reproducibility", "1-5", "Core criterion of scientific method (Popper, 1959)"),
            ("Study Design Quality", "1-5", "Evidence hierarchy per Cochrane Handbook"),
            ("Sample Size Adequacy", "adequate / inadequate", "Statistical power determines conclusion validity"),
            ("Power Calculation", "mentioned / not mentioned", "Required by CONSORT, often missing in practice"),
        ],
        "challenges": [
            ("Review papers have no methodology", "Agent is completely skipped for review papers and meta-analyses &mdash; prevents false low scores"),
            ("Numbers written as words", "&ldquo;ten hospitals&rdquo; and &ldquo;twenty-three participants&rdquo; must be recognized as sample size data &mdash; solved via LLM instruction + regex"),
            ("Sample sizes outside Methods", "Participant counts often appear in Abstract or Results, not Methods &mdash; agent receives all three sections as context"),
            ("Consistent evaluations across runs", "Temperature set to 0.3 (low) for reproducible scoring &mdash; same paper should get similar scores each time"),
        ],
        "poc_vs_prod": [
            ("Single GPT-4.1 call", "Multi-reviewer consensus (2-3 independent assessments)"),
            ("Free-text analysis", "CONSORT / STROBE / PRISMA checklist-based evaluation APIs"),
            ("LLM-based bias detection", "Cochrane Risk-of-Bias Tool (RoB 2) integration"),
            ("No structured data extraction", "Dedicated NLP for sample size and design extraction"),
        ],
        "economics": {
            "cost_per_paper": "~$0.02",
            "cost_details": "1 LLM call &bull; ~4K input + ~2K output tokens",
            "human_time": "1-2 hours",
            "human_desc": "for thorough methodology review",
            "agent_time": "~5 sec",
        },
    },

    # ----------------------------------------------------------
    # Agent 4: DataViz Critic
    # ----------------------------------------------------------
    "dataviz": {
        "icon": "📈",
        "title": "DataViz Critic",
        "what_it_does": """
Extracts and evaluates **every figure** in the PDF using computer vision.

Each figure is assessed on:
- **Chart type** — is it the right type for the data?
- **Color & colorblind accessibility** — distinguishable palettes?
- **Axes** — labels clear, scales appropriate, zero baseline?
- **Data-ink ratio** — chart junk, unnecessary 3D effects?
- **Legend** — present and useful?
- **Statistical elements** — error bars, sample sizes, significance?
- **Caption quality** — descriptive, standalone?
""",
        "how_it_works": [
            ("Step 1", "PyMuPDF extracts images from PDF pages"),
            ("Step 2", "Filter: min 50px, max 1024px, aspect ratio &lt; 10 (removes icons, separators)"),
            ("Step 3", "Resize large images (LANCZOS), encode as base64"),
            ("Step 4", "GPT-4.1 Vision analyzes each figure individually"),
            ("Step 5", "Separate LLM call analyzes captions and references in the text"),
            ("Step 6", "Synthesis: average scores, common patterns, best practice violations"),
        ],
        "intelligence": [
            "<b>Edward Tufte</b> &mdash; data-ink ratio principle: maximize data, minimize non-data ink (chart junk)",
            "<b>William Cleveland</b> &mdash; graphical perception research: humans read position &gt; length &gt; angle &gt; area",
            "<b>Stephen Few</b> &mdash; dashboard and chart design principles for clear data communication",
            "<b>Colorblind Accessibility</b> &mdash; ~8% of male readers are red-green colorblind; palettes must be distinguishable",
            "<b>12 Chart Types Recognized</b> &mdash; bar, line, scatter, pie, heatmap, box plot, histogram, forest plot, Kaplan-Meier, flowchart, table, diagram",
            "<b>Zero Baseline Principle</b> &mdash; bar charts must start at zero to avoid misleading visual comparisons",
            "<b>Error Bar &amp; Significance Standards</b> &mdash; scientific figures should show uncertainty (CI, SE, SD) where applicable",
        ],
        "metrics": [
            ("Color Usage", "1-5", "Tufte: color must encode information, not decoration"),
            ("Axis Assessment", "1-5", "Cleveland: axes determine perception accuracy"),
            ("Data-Ink Ratio", "1-5", "Tufte's core principle &mdash; every pixel should serve the data"),
            ("Legend Assessment", "1-5", "Few: legend must be clear and non-obstructive"),
            ("Caption Quality", "1-5", "Figures must be standalone &mdash; understandable without reading full paper"),
            ("Statistical Elements", "present / absent", "Error bars, n, significance markers &mdash; required in scientific publishing"),
            ("Colorblind Friendly", "yes / no", "Accessibility standard &mdash; ~8% male readers affected"),
            ("Overall Figure Score", "1-5", "Weighted average across applicable criteria"),
        ],
        "challenges": [
            ("Tiny images (icons, logos)", "Filtered out by MIN_IMAGE_DIMENSION=50px &mdash; prevents analyzing publisher logos as &ldquo;figures&rdquo;"),
            ("Line separators and decorative elements", "Filtered by aspect ratio &gt;10 &mdash; a 500x2px line is not a figure"),
            ("Duplicate images across pages", "Deduplicated by PDF xref ID &mdash; same image shown on two pages is analyzed only once"),
            ("RGBA images in JPEG format", "Automatic RGBA&rarr;RGB conversion prevents PIL/JPEG save errors"),
            ("Oversized images exceeding API limits", "LANCZOS resize to max 1024px while preserving quality"),
            ("Tables, diagrams, and flowcharts", "Criteria like axes and legend scored as N/A where not applicable &mdash; prevents false penalties"),
            ("Cost control with many figures", "MAX_FIGURES=20 cap prevents runaway API costs on figure-heavy papers"),
            ("Caption matching across naming conventions", "Fuzzy matching: &ldquo;Figure 1&rdquo;, &ldquo;Fig 1&rdquo;, &ldquo;Fig. 1&rdquo;, &ldquo;figure1&rdquo; all map correctly"),
            ("Dangling references", "Detects when text references figures that don't exist in the PDF"),
            ("Orphan figures", "Detects figures in PDF that are never referenced in the body text"),
        ],
        "poc_vs_prod": [
            ("PyMuPDF image extraction", "Dedicated CV model (YOLO / Detectron2) for chart region detection"),
            ("GPT-4.1 Vision analysis", "Claude Opus 4.6 Vision (higher visual reasoning accuracy)"),
            ("Simple pixel-based filtering", "WCAG accessibility compliance testing tools"),
            ("No OCR for text in figures", "Full OCR pipeline (Tesseract / EasyOCR) for axis labels and annotations"),
            ("LLM-based chart type detection", "Trained ML classifier for chart type recognition"),
        ],
        "economics": {
            "cost_per_paper": "~$0.05-0.15",
            "cost_details": "N+2 LLM calls (per figure + caption + synthesis) &bull; Vision API ~1K tokens/image",
            "human_time": "1-2 hours",
            "human_desc": "for thorough figure review against best practices",
            "agent_time": "~1-2 min",
        },
    },

    # ----------------------------------------------------------
    # Agent 5: Citation Hunter
    # ----------------------------------------------------------
    "citations": {
        "icon": "🔗",
        "title": "Citation Hunter",
        "what_it_does": """
Searches for related literature and evaluates how the paper fits into the broader research landscape.

The agent identifies:
- **Supporting papers** — confirming the paper's findings
- **Conflicting papers** — with possible explanations for discrepancies
- **Research gaps** — what the field still needs
- **Top relevant papers** — ranked by relevance (1-10 score)
""",
        "how_it_works": [
            ("Step 1", "Construct search query from paper title + abstract"),
            ("Step 2", "Search Semantic Scholar API (up to 10 results with metadata)"),
            ("Step 3", "LLM evaluates citation context, identifies support/conflict/gaps"),
        ],
        "intelligence": [
            "<b>Citation Context Analysis</b> &mdash; distinguishes supporting, conflicting, and tangentially related literature",
            "<b>Research Gap Identification</b> &mdash; systematic methodology for finding unanswered questions in a field",
            "<b>Literature Quality Assessment</b> &mdash; weak / moderate / strong based on volume, recency, and consistency of evidence",
            "<b>Relevance Scoring (1-10)</b> &mdash; multi-factor assessment: topic overlap, methodology similarity, recency",
        ],
        "metrics": [
            ("Supporting Papers", "list with relevance", "Standard in systematic literature reviews"),
            ("Conflicting Papers", "list with explanations", "Identifies where findings diverge from existing evidence"),
            ("Research Gaps", "list", "Core of academic contribution &mdash; what's still unknown"),
            ("Top Relevant Papers", "ranked 1-10", "Helps authors find potentially missing references"),
            ("Literature Quality", "weak / moderate / strong", "Overall embedding in research landscape"),
        ],
        "challenges": [
            ("Semantic Scholar rate limits (HTTP 429)", "Exponential backoff: 2s &rarr; 4s &rarr; 8s, max 3 retries &mdash; graceful degradation instead of crash"),
            ("No related papers found", "Graceful fallback with empty structure and clear &ldquo;unable to assess&rdquo; message"),
            ("Abstract truncation for token limits", "Related paper abstracts limited to 300 chars each &mdash; top 8 papers fit within context window"),
        ],
        "poc_vs_prod": [
            ("Semantic Scholar API (free, rate-limited)", "Scopus + Web of Science APIs ($$$$/year subscriptions)"),
            ("Single search query", "Multiple databases in parallel (CrossRef, PubMed, Google Scholar)"),
            ("Top 8 papers analyzed", "Full citation graph analysis with DOI-level matching"),
            ("Abstracts only", "Full-text similarity comparison"),
            ("1 LLM call for all analysis", "Per-paper relevance scoring + aggregate synthesis"),
        ],
        "economics": {
            "cost_per_paper": "~$0.02",
            "cost_details": "1 free API call (Semantic Scholar) + 1 LLM call",
            "human_time": "3-5 hours",
            "human_desc": "for thorough literature search and comparison",
            "agent_time": "~10 sec",
        },
    },

    # ----------------------------------------------------------
    # Agent 6: Plagiarism Detector
    # ----------------------------------------------------------
    "plagiarism": {
        "icon": "🚨",
        "title": "Plagiarism Detector",
        "what_it_does": """
Assesses academic integrity by analyzing the writing for:

- **Missing citations** — statements that need a source reference
- **Suspicious sections** — unusual style changes, potential borrowed text
- **Writing quality flags** — inconsistent tone, unexplained terminology
- **Risk level** — Low / Medium / High with numeric score (0-100)
""",
        "how_it_works": [
            ("Step 1", "Split text into sentences (filter &gt; 20 chars)"),
            ("Step 2", "Truncate to 50,000 characters if needed"),
            ("Step 3", "Select prompt based on paper type (original vs. review)"),
            ("Step 4", "LLM evaluates with structured JSON output"),
        ],
        "intelligence": [
            "<b>Paper-Type-Aware Evaluation</b> &mdash; completely different criteria for original research vs. review/meta-analysis",
            "<b>Review Papers ≠ Plagiarism</b> &mdash; reviews naturally paraphrase &mdash; the agent understands this and scores accordingly (0-30 unless verbatim copying)",
            "<b>Citation Pattern Recognition</b> &mdash; [1], [2,3], (4), (5,6) are correctly recognized as valid citation markers",
            "<b>Self-Plagiarism Indicators</b> &mdash; detects repetitive phrasing patterns and recycled content signs",
            "<b>Style Consistency Analysis</b> &mdash; sudden vocabulary or complexity shifts suggest copy-paste from multiple sources",
            "<b>Common Knowledge vs. Citable Claims</b> &mdash; distinguishes general facts from specific claims requiring references",
        ],
        "metrics": [
            ("Risk Score", "0-100", "Analogous to Turnitin Similarity Score &mdash; industry standard"),
            ("Risk Level", "low / medium / high", "Quick assessment for editorial decisions"),
            ("Missing Citations", "list with severity", "Concrete: which sentences need sources"),
            ("Suspicious Sections", "list with recommendations", "Style breaks indicating potential copy-paste"),
            ("Writing Quality Flags", "list", "Inconsistent tone as an integrity indicator"),
        ],
        "challenges": [
            ("Review paper false positives (BIGGEST challenge)", "Reviews summarize literature &mdash; initial version flagged this as plagiarism. Solution: dedicated review-aware prompt with explicit instruction to score LOW (0-30) unless actual verbatim copying detected"),
            ("Citation pattern recognition", "Numbered references like [1], [2,3], (4) must be recognized as valid citations &mdash; not flagged as &ldquo;uncited claims&rdquo;"),
            ("Long papers exceeding token limits", "Truncation to 50,000 characters preserves analysis quality while staying within API limits"),
            ("Short sentence fragments", "Headers, figure labels, and fragments &lt;20 chars filtered out to avoid noise"),
        ],
        "poc_vs_prod": [
            ("LLM-based heuristic analysis (no database)", "Turnitin / iThenticate API (~$3/paper, real text database)"),
            ("No internet search", "Copyscape / CrossCheck with web crawling"),
            ("Style analysis per LLM", "Dedicated authorship attribution ML models"),
            ("Single-pass assessment", "Multi-pass with fingerprinting and n-gram matching"),
        ],
        "economics": {
            "cost_per_paper": "~$0.03",
            "cost_details": "1 LLM call &bull; large input (~50K chars)",
            "human_time": "not possible",
            "human_desc": "humans cannot detect plagiarism without tools &mdash; Turnitin costs ~$3/paper",
            "agent_time": "~5 sec",
        },
    },

    # ----------------------------------------------------------
    # Agent 7: Journal Recommender
    # ----------------------------------------------------------
    "journals": {
        "icon": "📚",
        "title": "Journal Recommender",
        "what_it_does": """
Recommends target journals for publication using **real journal metrics** from OpenAlex combined with LLM-powered fit assessment.

For each journal provides:
- Journal name, publisher, homepage
- **Impact Factor (2yr)** and **h-index** (real data from OpenAlex)
- Open Access status and APC (Article Processing Charge)
- Scope fit reasoning and acceptance likelihood
- Number of similar papers found in that journal
""",
        "how_it_works": [
            ("Step 1", "LLM extracts 3 search queries from title + abstract (topic, method, niche)"),
            ("Step 2", "Search OpenAlex for similar works &rarr; aggregate source journals by frequency"),
            ("Step 3", "LLM suggests field-specific journals &rarr; verify each in OpenAlex"),
            ("Step 4", "Fetch details for top 12 by frequency + all LLM suggestions"),
            ("Step 5", "Compute composite relevance score: <code>IF &times; 3.0 + h_index &times; 0.1 + frequency &times; 2.0</code>"),
            ("Step 6", "LLM ranks with personalized reasoning, split into primary &amp; secondary"),
        ],
        "intelligence": [
            "<b>Composite Relevance Formula</b> &mdash; <code>score = IF &times; 3.0 + h_index &times; 0.1 + frequency &times; 2.0</code> &mdash; weights impact highest, then prior publication frequency",
            "<b>Mega-Journal Detection</b> &mdash; journals with &gt;50K works (IEEE Access, Sustainability, PLOS ONE) automatically demoted to secondary recommendations",
            "<b>Two-Source Strategy</b> &mdash; frequency-based (where similar papers published) + LLM-suggested (field-specific knowledge) &rarr; deduplicated for comprehensive coverage",
            "<b>Journal Landscape Knowledge</b> &mdash; LLM trained on knowledge of journals across all research fields",
            "<b>Acceptance Likelihood Assessment</b> &mdash; factors in paper quality (methodology score, evidence strength) when estimating chances",
            "<b>Scope Fit Evaluation</b> &mdash; excellent / good / moderate assessment for each journal",
        ],
        "metrics": [
            ("Impact Factor (2yr)", "number", "Standard bibliometric measure from JCR (Journal Citation Reports)"),
            ("h-index", "number", "Robust impact indicator (Hirsch, 2005) &mdash; complementary to IF"),
            ("Open Access + APC", "yes/no + USD", "Practical decision criteria for authors"),
            ("Scope Fit", "excellent / good / moderate", "Most important factor for acceptance"),
            ("Acceptance Likelihood", "high / medium / low", "Based on paper quality context"),
            ("Publication Strategy", "text", "Strategic submission order advice"),
            ("Reviewer Concerns", "list", "What reviewers might flag &mdash; helps authors prepare"),
        ],
        "challenges": [
            ("Mega-journal bias in frequency results", "IEEE Access, Sustainability, PLOS ONE dominate because they publish everything &mdash; explicitly demoted to secondary with works_count &gt;50K filter"),
            ("LLM hallucination of non-existent journals", "Every LLM-suggested journal is verified against OpenAlex before inclusion &mdash; unverified suggestions discarded"),
            ("OpenAlex data unavailable", "Graceful fallback to LLM-only recommendations with &ldquo;low&rdquo; confidence flag"),
            ("Query diversity for broad coverage", "3 different search angles (topic, methodology, niche) ensure diverse journal candidates"),
            ("Rate limiting on OpenAlex", "0.15-0.2s sleep between API calls prevents 429 errors"),
            ("Deduplication across sources", "Frequency-based and LLM-suggested journals merged by OpenAlex source ID"),
        ],
        "poc_vs_prod": [
            ("OpenAlex API (free, open data)", "Scopus / Web of Science APIs ($$$$/ year subscriptions)"),
            ("GPT-4.1 for ranking", "JCR (Journal Citation Reports) official data"),
            ("Custom relevance formula", "Elsevier Journal Finder / Springer Journal Suggester"),
            ("~20 journals analyzed", "Thousands of journals with real submission analytics"),
            ("No acceptance rate data", "Historical acceptance rate statistics per journal"),
        ],
        "economics": {
            "cost_per_paper": "~$0.04",
            "cost_details": "3 LLM calls + ~20 OpenAlex calls (free)",
            "human_time": "4-8 hours",
            "human_desc": "for thorough journal research and comparison",
            "agent_time": "~1-2 min",
        },
    },

    # ----------------------------------------------------------
    # Agent 8: Funding Advisor
    # ----------------------------------------------------------
    "funding": {
        "icon": "💰",
        "title": "Funding Advisor",
        "what_it_does": """
Identifies potential funding sources by analyzing which organizations have funded similar research.

For each funder provides:
- Organization name, country, homepage
- **Relevance** with reasoning
- Known programs and typical grant amounts
- Typical duration and eligibility notes
- Concrete application tips
""",
        "how_it_works": [
            ("Step 1", "LLM extracts 3 search queries from title + abstract"),
            ("Step 2", "Search OpenAlex for similar works &rarr; extract funder data from each paper"),
            ("Step 3", "Calculate field-wide funding rate (what % of similar papers were funded)"),
            ("Step 4", "Get top 15 funders by frequency across all search results"),
            ("Step 5", "Fetch funder details + sample award amounts from OpenAlex"),
            ("Step 6", "LLM ranks and enriches with program knowledge, eligibility, tips"),
        ],
        "intelligence": [
            "<b>Global Funding Program Knowledge</b> &mdash; DFG, NIH, ERC, NSF, EPSRC, NSERC, ARC and many more &mdash; knows program names, typical amounts, eligibility",
            "<b>Eligibility Criteria per Funder</b> &mdash; e.g., &ldquo;PI must be at a German university&rdquo; (DFG) or &ldquo;early career only&rdquo; (ERC Starting Grant)",
            "<b>Typical Grant Amounts &amp; Durations</b> &mdash; contextualizes recommendations (e.g., NIH R01: $250K-$500K/yr, 3-5 years)",
            "<b>Application Tips</b> &mdash; practical advice based on funder expectations and review culture",
            "<b>Funding Rate Calculation</b> &mdash; computes what % of similar papers in the field were funded &mdash; gives context for the research area",
            "<b>Award Data Interpretation</b> &mdash; knows that NSF/FAPESP have amount data, while Crossref-sourced records often don&rsquo;t",
        ],
        "metrics": [
            ("Primary Funders", "3-5 ranked", "Top matches who actively fund this type of research"),
            ("Secondary Funders", "3-5 ranked", "Additional options &mdash; regional, smaller, or more competitive"),
            ("Programs, Amounts, Duration", "per funder", "Practical planning data for grant applications"),
            ("Eligibility Notes", "per funder", "Prevents wasted applications to ineligible programs"),
            ("Funding Rate in Field", "percentage", "Context: how well funded is this research area overall"),
            ("Data Confidence", "high / medium / low", "Honest assessment of how much data backs the recommendation"),
        ],
        "challenges": [
            ("Award amounts mostly unavailable", "Only NSF and FAPESP-sourced data includes amounts; Crossref-sourced records typically have no amount field &mdash; honestly communicated in results"),
            ("Funding rate as context metric", "Calculated field-wide across all search results &mdash; gives authors realistic expectations for their area"),
            ("Funder ID handling", "OpenAlex uses F-prefixed IDs that must be extracted and reformatted for API endpoint calls"),
            ("No funders found in search results", "Graceful fallback with alternative tool suggestions (ELFI, GrantForward) instead of empty results"),
            ("Hybrid enrichment approach", "Real funder data from OpenAlex (who actually funded similar work) + LLM knowledge about programs and amounts = more useful than either alone"),
        ],
        "poc_vs_prod": [
            ("OpenAlex funder data (free, open)", "Dimensions.ai ($$$ &mdash; comprehensive funder database)"),
            ("GPT-4.1 enrichment", "GrantForward / Pivot-RP ($$$ &mdash; dedicated funding search tools)"),
            ("No live deadline data", "Live deadline tracking and notification system"),
            ("Generic eligibility info", "Institutional eligibility matching (checks your university's agreements)"),
            ("No application templates", "Pre-filled application templates per funder program"),
        ],
        "economics": {
            "cost_per_paper": "~$0.04",
            "cost_details": "2 LLM calls + ~20 OpenAlex calls (free)",
            "human_time": "5-10 hours",
            "human_desc": "for thorough funding research and program matching",
            "agent_time": "~1-2 min",
        },
    },
}


# ═══════════════════════════════════════════════════════════════
# Render Function — standardized 6-section layout for all agents
# ═══════════════════════════════════════════════════════════════

def render_agent_page(key):
    agent = AGENT_DATA[key]

    # --- Section 1: What it does + How it works ---
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### What It Does")
        st.markdown(agent["what_it_does"])
    with col2:
        st.markdown("#### How It Works")
        for label, text in agent["how_it_works"]:
            st.markdown(
                f'<div class="pipeline-step"><b>{label}:</b> {text}</div>',
                unsafe_allow_html=True,
            )

    # --- Section 2: Intelligence Built In ---
    st.markdown(
        '<div class="section-head">🧠 Intelligence Built In</div>',
        unsafe_allow_html=True,
    )
    for item in agent["intelligence"]:
        st.markdown(
            f'<div class="intel-item">{item}</div>',
            unsafe_allow_html=True,
        )

    # --- Section 3: Metrics Produced ---
    st.markdown(
        '<div class="section-head">📏 Metrics Produced</div>',
        unsafe_allow_html=True,
    )
    table = "| Metric | Type / Scale | Why This Metric? |\n"
    table += "|--------|-------------|------------------|\n"
    for metric, scale, why in agent["metrics"]:
        table += f"| {metric} | {scale} | {why} |\n"
    st.markdown(table)

    # --- Section 4: Special Challenges Solved ---
    st.markdown(
        '<div class="section-head">🔧 Special Challenges Solved</div>',
        unsafe_allow_html=True,
    )
    for title, desc in agent["challenges"]:
        st.markdown(
            f'<div class="challenge-item"><b>{title}</b> &mdash; {desc}</div>',
            unsafe_allow_html=True,
        )

    # --- Section 5: Proof of Concept vs. Production Grade ---
    st.markdown(
        '<div class="section-head">🔬 Proof of Concept vs. Production Grade</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "*This is a Proof of Concept built on a minimal budget. "
        "The comparison shows what we built vs. what a fully funded production solution would use "
        "— demonstrating awareness of the optimal approach.*"
    )
    table = "| Our PoC Approach | Production-Grade Alternative |\n"
    table += "|-----------------|-----------------------------|\n"
    for poc, prod in agent["poc_vs_prod"]:
        table += f"| {poc} | {prod} |\n"
    st.markdown(table)

    # --- Section 6: Economics (Cost + ROI) ---
    st.markdown(
        '<div class="section-head">💰 Economics</div>',
        unsafe_allow_html=True,
    )
    econ = agent["economics"]
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="econ-card">
            <div class="econ-value">{econ["cost_per_paper"]}</div>
            <div class="econ-label">API Cost per Paper</div>
            <div class="econ-detail">{econ["cost_details"]}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="econ-card">
            <div class="econ-value">{econ["agent_time"]}</div>
            <div class="econ-label">Agent Processing Time</div>
            <div class="econ-detail">vs. {econ["human_time"]} manual review</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="econ-card">
            <div class="econ-value">{econ["human_time"]}</div>
            <div class="econ-label">Human Expert Equivalent</div>
            <div class="econ-detail">{econ["human_desc"]}</div>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# Page Routing
# ═══════════════════════════════════════════════════════════════

NAV_TO_KEY = {
    AGENT_NAV[1]: "results",
    AGENT_NAV[2]: "writing",
    AGENT_NAV[3]: "methodology",
    AGENT_NAV[4]: "dataviz",
    AGENT_NAV[5]: "citations",
    AGENT_NAV[6]: "plagiarism",
    AGENT_NAV[7]: "journals",
    AGENT_NAV[8]: "funding",
}


# --- Architecture Overview ---
if selected_agent == AGENT_NAV[0]:
    st.markdown("""
    <div class="arch-grid">
        <div class="arch-box">
            <h4>Analysis Pipeline</h4>
            <p>When you upload a PDF, the Paper Analyzer runs a multi-step pipeline:</p>
            <div class="pipeline-step"><b>Step 1:</b> PDF text extraction (pypdf)</div>
            <div class="pipeline-step"><b>Step 2:</b> Section detection &mdash; LLM identifies Abstract, Introduction, Methods, Results, Discussion, Conclusion</div>
            <div class="pipeline-step"><b>Step 3:</b> Paper type classification &mdash; original research, review, meta-analysis, or case study</div>
            <div class="pipeline-step"><b>Step 4:</b> 8 specialized agents analyze the paper in parallel/sequence</div>
            <div class="pipeline-step"><b>Step 5:</b> Results aggregated into an interactive dashboard &amp; downloadable report</div>
        </div>
        <div class="arch-box">
            <h4>Tech Stack</h4>
            <p>
                <span class="tech-badge llm">Azure OpenAI GPT-4.1</span><br>
                <span class="tech-badge api">Semantic Scholar API</span><br>
                <span class="tech-badge api">OpenAlex API</span><br>
                <span class="tech-badge python">PyMuPDF (fitz)</span><br>
                <span class="tech-badge python">pypdf</span><br>
                <span class="tech-badge">Streamlit</span>
            </p>
            <h4 style="margin-top: 1rem;">Paper Types</h4>
            <p style="font-size: 0.9rem;">
                Original Research &bull; Review Articles<br>
                Meta-Analyses &bull; Case Studies
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### Agent Overview")
    st.markdown("""
    | # | Agent | Technology | Primary Output |
    |---|-------|-----------|----------------|
    | 1 | Results Synthesizer | GPT-4.1 | Evidence strength (weak/moderate/strong) |
    | 2 | Writing Coach | GPT-4.1 + Python regex | Writing score (1-5) + Readability level |
    | 3 | Methodology Critic | GPT-4.1 | Quality score (1-5) |
    | 4 | DataViz Critic | GPT-4.1 Vision + PyMuPDF | Figure scores (1-5) |
    | 5 | Citation Hunter | GPT-4.1 + Semantic Scholar | Literature quality |
    | 6 | Plagiarism Detector | GPT-4.1 + Python regex | Risk score (0-100) |
    | 7 | Journal Recommender | GPT-4.1 + OpenAlex | Journal matches + confidence |
    | 8 | Funding Advisor | GPT-4.1 + OpenAlex | Funder matches + confidence |
    """)

    st.markdown("#### Total Economics (all 8 agents combined)")
    st.markdown("""
    <table>
        <tr><th></th><th>Our Proof of Concept</th><th>Human Expert</th></tr>
        <tr><td><b>Hourly Rate</b></td><td>n/a (API cost only)</td><td>$50 – $100/hr (qualified reviewer)</td></tr>
        <tr><td><b>Time per Paper</b></td><td>~3 – 5 minutes</td><td>~20 – 40 hours (all 8 aspects)</td></tr>
        <tr><td><b>Cost per Paper</b></td><td>~$0.15 – $0.35</td><td>$1,000 – $4,000 (= time &times; rate)</td></tr>
        <tr><td><b>Monthly Cost (50 papers)</b></td><td>~$7.50 – $17.50</td><td>$50,000 – $200,000</td></tr>
        <tr><td><b>External APIs</b></td><td>All free (Semantic Scholar, OpenAlex)</td><td>Scopus, Web of Science, Turnitin ($$$)</td></tr>
    </table>
    """, unsafe_allow_html=True)


# --- Agent pages ---
else:
    agent_key = NAV_TO_KEY.get(selected_agent)
    if agent_key:
        render_agent_page(agent_key)


# ═══════════════════════════════════════════════════════════════
# Footer
# ═══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem; padding: 1rem 0;">
    <b>Paper Analyzer</b> &mdash; 8 AI Agents for Comprehensive Research Paper Analysis<br>
    Powered by Azure OpenAI &bull; Semantic Scholar &bull; OpenAlex &bull; PyMuPDF<br>
    <br>
    <span style="font-size: 0.8rem; opacity: 0.7;">
        Go to the main page to analyze a paper &rarr;
    </span>
</div>
""", unsafe_allow_html=True)
