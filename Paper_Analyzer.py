import streamlit as st
import tempfile
import os
import sys
import json
import io
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime

# Page config must be first Streamlit command
st.set_page_config(
    page_title="Paper Analyzer",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Agent Selection Config ---
AGENT_OPTIONS = {
    "results": "📊 Results Synthesizer",
    "writing": "✍️ Writing Coach",
    "methodology": "🔬 Methodology Critic",
    "visualization": "📈 DataViz Critic",
    "citations": "🔗 Citation Hunter",
    "plagiarism": "🚨 Plagiarism Detector",
    "journals": "📚 Journal Recommender",
    "funding": "💰 Funding Advisor",
}
ALL_AGENT_KEYS = list(AGENT_OPTIONS.keys())

def _skipped_data(agent_key):
    """Return empty fallback data for a skipped agent"""
    base = {"_skipped": True}
    if agent_key == "methodology":
        base.update({"sample_size": {"n": "N/A", "adequate": True, "power_calculation": "N/A", "comment": "Agent not selected"}, "study_design": {"type": "N/A", "quality_score": "N/A", "appropriateness": "N/A"}, "statistical_methods": {"methods_used": [], "appropriate": True, "issues": []}, "biases": {"identified": [], "addressed": True, "comment": "N/A"}, "reproducibility": {"score": "N/A", "comment": "N/A"}, "overall_quality": "N/A", "critical_issues": [], "strengths": []})
    elif agent_key == "results":
        base.update({"primary_outcome": {"measure": "N/A", "result": "N/A", "statistically_significant": False, "p_value": "N/A"}, "key_findings": [], "effect_sizes": [], "secondary_outcomes": [], "main_conclusion": "Agent not selected", "strength_of_evidence": "unknown", "limitations_noted": []})
    elif agent_key == "visualization":
        base.update({"figures_analyzed": 0, "overall_quality": "N/A", "overall_assessment": "Agent not selected", "figure_analyses": [], "common_patterns": [], "best_practice_violations": [], "strengths": [], "recommendations": [], "visualization_strategy": "", "caption_analysis": {}})
    elif agent_key == "writing":
        base.update({"overall_writing_score": "N/A", "overall_assessment": "Agent not selected", "sections": {}, "quantitative_metrics": {}, "cross_section_patterns": [], "top_improvements": [], "style_guide_references": [], "readability_level": "N/A", "data_confidence": "N/A"})
    elif agent_key == "citations":
        base.update({"supporting_papers": [], "conflicting_papers": [], "research_gaps": [], "top_relevant": [], "literature_quality": "unknown", "citation_context": "Agent not selected"})
    elif agent_key == "plagiarism":
        base.update({"plagiarism_risk_score": "N/A", "risk_level": "unknown", "missing_citations": [], "suspicious_sections": [], "writing_quality_flags": [], "overall_assessment": "Agent not selected", "recommendations": []})
    elif agent_key == "journals":
        base.update({"primary_recommendations": [], "secondary_recommendations": [], "publication_strategy": "", "key_strengths_for_submission": [], "potential_concerns_for_reviewers": [], "recommendation_confidence": "unknown", "search_queries_used": [], "journals_found": 0})
    elif agent_key == "funding":
        base.update({"primary_funders": [], "secondary_funders": [], "funding_strategy": "", "funding_landscape": "", "total_similar_funded_papers": 0, "data_confidence": "unknown", "search_queries_used": [], "funders_found": 0})
    return base

# --- Custom CSS: Green tones, positive feeling ---
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #f0faf0 0%, #e8f5e9 50%, #f1f8e9 100%);
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1b5e20 0%, #2e7d32 40%, #388e3c 100%);
    }
    section[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p {
        color: #e8f5e9 !important;
    }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
        color: #ffffff !important;
    }

    /* Page navigation links (App / How It Works) */
    [data-testid="stSidebarNav"] {
        background: white;
        border-radius: 12px;
        padding: 0.8rem 0.5rem;
        margin: 0.5rem 0.8rem 1rem 0.8rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    [data-testid="stSidebarNav"] a {
        color: #1b5e20 !important;
        font-size: 1.3rem !important;
        font-weight: 700 !important;
        padding: 0.6rem 1rem !important;
        border-radius: 8px;
        transition: background 0.2s ease;
    }
    [data-testid="stSidebarNav"] a:hover {
        background: #e8f5e9 !important;
    }
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: #e8f5e9 !important;
        color: #1b5e20 !important;
    }
    [data-testid="stSidebarNav"] a span {
        color: #1b5e20 !important;
        font-size: 1.3rem !important;
        font-weight: 700 !important;
    }

    /* Header area */
    .main-header {
        background: linear-gradient(90deg, #2e7d32, #43a047, #66bb6a);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px rgba(46, 125, 50, 0.3);
    }
    .main-header h1 {
        color: white !important;
        font-size: 2.2rem !important;
        margin-bottom: 0.3rem !important;
    }
    .main-header p {
        color: #c8e6c9 !important;
        font-size: 1.1rem !important;
        margin: 0 !important;
    }

    /* Metric cards — equal height row */
    [data-testid="stHorizontalBlock"]:has(.metric-card) {
        align-items: stretch !important;
    }
    [data-testid="stHorizontalBlock"]:has(.metric-card) [data-testid="stColumn"] > div {
        height: 100% !important; display: flex !important; flex-direction: column !important;
    }
    [data-testid="stHorizontalBlock"]:has(.metric-card) [data-testid="stColumn"] > div > div {
        flex: 1 !important; display: flex !important; flex-direction: column !important;
    }
    [data-testid="stHorizontalBlock"]:has(.metric-card) [data-testid="stColumn"] > div > div > div {
        flex: 1 !important; display: flex !important;
    }
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 4px solid #43a047;
        display: flex;
        flex-direction: column;
        justify-content: center;
        flex: 1;
    }
    .metric-card .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #2e7d32;
    }
    .metric-card .metric-label {
        font-size: 0.85rem;
        color: #666;
        margin-top: 0.3rem;
    }

    /* Agent section cards */
    .agent-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
        border-top: 3px solid #43a047;
    }

    /* Success/positive elements */
    .success-badge {
        background: #e8f5e9;
        color: #2e7d32;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }
    .warning-badge {
        background: #fff8e1;
        color: #f57f17;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }
    .danger-badge {
        background: #fce4ec;
        color: #c62828;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }

    /* Progress animation */
    .progress-step {
        background: white;
        border-radius: 10px;
        padding: 0.8rem 1.2rem;
        margin: 0.4rem 0;
        display: flex;
        align-items: center;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    .progress-step.active {
        border-left: 3px solid #43a047;
        background: #f1f8e9;
    }
    .progress-step.done {
        border-left: 3px solid #81c784;
        opacity: 0.85;
    }

    /* Journal recommendation cards */
    .journal-card {
        background: white;
        border-radius: 10px;
        padding: 1.2rem;
        margin: 0.5rem 0;
        box-shadow: 0 1px 6px rgba(0,0,0,0.08);
        border-left: 4px solid #66bb6a;
    }
    .journal-card.secondary {
        border-left-color: #a5d6a7;
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #e8f5e9;
        border-radius: 8px 8px 0 0;
        padding: 0.5rem 1.2rem;
        color: #2e7d32;
    }
    .stTabs [aria-selected="true"] {
        background-color: #43a047 !important;
        color: white !important;
    }

    /* Upload area */
    .stFileUploader > div {
        border: 2px dashed #81c784 !important;
        border-radius: 12px !important;
        background: #f1f8e9 !important;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #43a047, #66bb6a) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 2rem !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 8px rgba(67, 160, 71, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        box-shadow: 0 4px 12px rgba(67, 160, 71, 0.6) !important;
        transform: translateY(-1px) !important;
    }

    /* Download button */
    .stDownloadButton > button {
        background: linear-gradient(90deg, #2e7d32, #43a047) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: #f1f8e9 !important;
        border-radius: 8px !important;
    }

    /* Hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Smooth scrolling */
    html { scroll-behavior: smooth; }
</style>
""", unsafe_allow_html=True)


def get_badge(level, invert=False):
    """Return colored badge HTML based on level.

    invert=True for metrics where LOW is good / HIGH is bad (e.g. plagiarism risk).
    """
    level_upper = str(level).upper()

    # Always positive (green)
    POSITIVE = {"STRONG", "EXCELLENT", "ADVANCED ACADEMIC", "ACADEMIC", "ACCESSIBLE", "ACCESSIBLE ACADEMIC"}
    # Always negative (red)
    NEGATIVE = {"WEAK", "POOR", "CRITICAL", "NONE"}
    # Always neutral (yellow)
    NEUTRAL = {"MODERATE", "MEDIUM", "GOOD", "GENERAL", "BASIC ACADEMIC", "SPECIALIZED", "EXPERT ONLY", "MIXED"}

    if level_upper in POSITIVE:
        return f'<span class="success-badge">{level_upper}</span>'
    if level_upper in NEGATIVE:
        return f'<span class="danger-badge">{level_upper}</span>'
    if level_upper in NEUTRAL:
        return f'<span class="warning-badge">{level_upper}</span>'

    # HIGH/LOW depend on context
    if level_upper == "HIGH":
        if invert:
            return f'<span class="danger-badge">{level_upper}</span>'
        return f'<span class="success-badge">{level_upper}</span>'
    if level_upper == "LOW":
        if invert:
            return f'<span class="success-badge">{level_upper}</span>'
        return f'<span class="danger-badge">{level_upper}</span>'

    # Unknown / unrecognized → neutral gray
    return f'<span class="warning-badge">{level_upper}</span>'


def get_score_color(score, max_val=5):
    """Return color based on score"""
    if score == "N/A":
        return "#888"
    try:
        ratio = float(score) / float(max_val)
        if ratio >= 0.7:
            return "#2e7d32"
        elif ratio >= 0.4:
            return "#f57f17"
        else:
            return "#c62828"
    except (ValueError, TypeError):
        return "#888"


def render_header():
    """Render the main header"""
    st.markdown("""
    <div class="main-header">
        <h1>🔬 Research Paper Analyzer</h1>
        <p>AI-powered analysis with 8 specialized agents — Upload your paper and get instant feedback</p>
    </div>
    """, unsafe_allow_html=True)



def render_sidebar():
    """Render sidebar with info and agent selection"""
    with st.sidebar:
        # --- Agent Selection ---
        st.markdown("### Select Agents")
        run_all = st.checkbox("Run all agents", value=True, key="run_all_agents")

        selected_agents = []
        for key, label in AGENT_OPTIONS.items():
            checked = st.checkbox(label, value=run_all or True, key=f"agent_{key}",
                                  disabled=run_all)
            if run_all or checked:
                selected_agents.append(key)

        # Store in session state for access by run_analysis
        st.session_state.selected_agents = selected_agents

        n_selected = len(selected_agents)
        st.caption(f"{n_selected} of 8 agents selected")

        st.markdown("---")
        st.markdown("""
        ### Supported paper types
        - Original Research
        - Review Articles
        - Meta-Analyses
        - Case Studies
        """)
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; opacity: 0.7; font-size: 0.85rem;">
            Powered by Azure OpenAI<br>
            OpenAlex & Semantic Scholar<br>
            8 AI Agents
        </div>
        """, unsafe_allow_html=True)


def render_summary_metrics(methods, results, plagiarism, journals, visualization=None, writing=None):
    """Render the summary metric cards at the top"""
    cols = st.columns(7)

    quality = methods.get('overall_quality', 'N/A')
    quality_display = f"{quality}/5" if quality != "N/A" else "N/A"

    evidence = results.get('strength_of_evidence', 'unknown').upper()

    plag_score = plagiarism.get('plagiarism_risk_score', 'N/A')
    plag_level = plagiarism.get('risk_level', 'unknown').upper()

    top_journal = journals.get('primary_recommendations', [{}])[0].get('journal_name', 'N/A') if journals.get('primary_recommendations') else 'N/A'
    confidence = journals.get('recommendation_confidence', 'unknown').upper()

    with cols[0]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{get_badge(evidence)}</div>
            <div class="metric-label">Evidence Strength</div>
        </div>
        """, unsafe_allow_html=True)

    with cols[1]:
        writing_score = writing.get('overall_writing_score', 'N/A') if writing else 'N/A'
        writing_display = f"{writing_score}/5" if writing_score != "N/A" else "N/A"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: {get_score_color(writing_score)}">{writing_display}</div>
            <div class="metric-label">Writing Quality</div>
        </div>
        """, unsafe_allow_html=True)

    with cols[2]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: {get_score_color(quality)}">{quality_display}</div>
            <div class="metric-label">Methodology Quality</div>
        </div>
        """, unsafe_allow_html=True)

    with cols[3]:
        dataviz_quality = visualization.get('overall_quality', 'N/A') if visualization else 'N/A'
        dataviz_display = f"{dataviz_quality}/5" if dataviz_quality != "N/A" else "N/A"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: {get_score_color(dataviz_quality)}">{dataviz_display}</div>
            <div class="metric-label">DataViz Quality</div>
        </div>
        """, unsafe_allow_html=True)

    with cols[4]:
        plag_color = "#2e7d32" if plag_score != "N/A" and int(plag_score) < 30 else ("#f57f17" if plag_score != "N/A" and int(plag_score) < 60 else "#c62828")
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: {plag_color}">{plag_score}/100</div>
            <div class="metric-label">Plagiarism Risk ({plag_level})</div>
        </div>
        """, unsafe_allow_html=True)

    with cols[5]:
        # Truncate long journal names
        journal_short = top_journal[:20] + "..." if len(top_journal) > 20 else top_journal
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="font-size: 1rem; color: #2e7d32;">{journal_short}</div>
            <div class="metric-label">Top Journal Match</div>
        </div>
        """, unsafe_allow_html=True)

    with cols[6]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{get_badge(confidence)}</div>
            <div class="metric-label">Recommendation Confidence</div>
        </div>
        """, unsafe_allow_html=True)


def render_methodology_tab(methods):
    """Render Agent 1 results"""
    quality = methods.get('overall_quality', 'N/A')

    st.markdown(f"### Overall Quality: {quality}/5")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Sample Size")
        sample = methods.get('sample_size', {})
        st.markdown(f"- **N:** {sample.get('n', 'N/A')}")
        adequate = sample.get('adequate', False)
        st.markdown(f"- **Adequate:** {'Yes' if adequate else 'No'}")
        st.markdown(f"- **Power Calculation:** {sample.get('power_calculation', 'N/A')}")
        if sample.get('comment'):
            st.info(sample['comment'])

        st.markdown("#### Study Design")
        design = methods.get('study_design', {})
        st.markdown(f"- **Type:** {design.get('type', 'N/A')}")
        st.markdown(f"- **Quality:** {design.get('quality_score', 'N/A')}/5")
        if design.get('appropriateness'):
            st.markdown(f"- **Appropriateness:** {design['appropriateness']}")

    with col2:
        st.markdown("#### Statistical Methods")
        stats = methods.get('statistical_methods', {})
        used = stats.get('methods_used', [])
        if used:
            for m in used:
                st.markdown(f"- {m}")
        else:
            st.markdown("_None identified_")
        appropriate = stats.get('appropriate', False)
        st.markdown(f"- **Appropriate:** {'Yes' if appropriate else 'No'}")

        st.markdown("#### Reproducibility")
        repro = methods.get('reproducibility', {})
        st.markdown(f"**Score:** {repro.get('score', 'N/A')}/5")
        if repro.get('comment'):
            st.caption(repro['comment'])

    # Critical Issues
    issues = methods.get('critical_issues', [])
    if issues:
        st.markdown("#### Critical Issues")
        for issue in issues:
            st.warning(issue)

    # Strengths
    strengths = methods.get('strengths', [])
    if strengths:
        st.markdown("#### Strengths")
        for s in strengths:
            st.success(s)

    # Biases
    biases = methods.get('biases', {})
    identified = biases.get('identified', [])
    if identified:
        st.markdown("#### Identified Biases")
        for b in identified:
            st.markdown(f"- {b}")
        if biases.get('comment'):
            st.caption(biases['comment'])


def render_results_tab(results):
    """Render Agent 2 results"""
    primary = results.get('primary_outcome', {})
    st.markdown(f"**Primary Outcome:** {primary.get('measure', 'N/A')}")
    st.markdown(f"> {primary.get('result', 'N/A')}")

    sig = primary.get('statistically_significant', False)
    pval = primary.get('p_value', 'N/A')
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Statistically Significant:** {'Yes' if sig else 'No'}")
    with col2:
        st.markdown(f"**P-value:** {pval}")

    # Main Findings
    findings = results.get('key_findings', [])
    if findings:
        st.markdown("#### Main Findings")
        for i, f in enumerate(findings):
            with st.expander(f"Finding {i+1}: {f.get('finding', 'N/A')[:80]}..."):
                st.markdown(f"**Statistic:** {f.get('statistic', 'N/A')}")
                st.markdown(f"**P-value:** {f.get('p_value', 'N/A')}")
                st.markdown(f"**CI:** {f.get('confidence_interval', 'N/A')}")

    # Effect Sizes
    effects = results.get('effect_sizes', [])
    if effects:
        st.markdown("#### Effect Sizes")
        for e in effects:
            interpretation = e.get('interpretation', '')
            badge = get_badge("STRONG" if "large" in interpretation.lower() else ("MODERATE" if "medium" in interpretation.lower() else "LOW"))
            st.markdown(f"- **{e.get('metric', 'N/A')}:** {e.get('value', 'N/A')} ({interpretation}) — {e.get('clinical_significance', '')}", unsafe_allow_html=True)

    # Secondary Outcomes
    secondary = results.get('secondary_outcomes', [])
    if secondary:
        st.markdown("#### Secondary Outcomes")
        for o in secondary:
            st.markdown(f"- **{o.get('outcome', 'N/A')}:** {o.get('result', 'N/A')}")

    # Conclusion
    st.markdown("---")
    conclusion = results.get('main_conclusion', 'N/A')
    st.markdown(f"**Main Conclusion:** {conclusion}")
    evidence = results.get('strength_of_evidence', 'unknown')
    st.markdown(f"**Strength of Evidence:** {get_badge(evidence)}", unsafe_allow_html=True)


def render_citations_tab(citations):
    """Render Agent 3 results"""
    quality = citations.get('literature_quality', 'unknown')
    st.markdown(f"**Literature Quality:** {get_badge(quality)}", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Supporting Evidence")
        supporting = citations.get('supporting_papers', [])
        if supporting:
            for p in supporting:
                st.markdown(f"""
                <div style="background: #e8f5e9; padding: 0.8rem; border-radius: 8px; margin: 0.4rem 0; border-left: 3px solid #43a047;">
                    <strong>{p.get('title', 'N/A')}</strong> ({p.get('year', 'N/A')})<br>
                    <span style="color: #555; font-size: 0.9rem;">{p.get('relevance', '')}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No supporting papers identified")

    with col2:
        st.markdown("#### Conflicting Evidence")
        conflicting = citations.get('conflicting_papers', [])
        if conflicting:
            for p in conflicting:
                st.markdown(f"""
                <div style="background: #fff8e1; padding: 0.8rem; border-radius: 8px; margin: 0.4rem 0; border-left: 3px solid #ffa000;">
                    <strong>{p.get('title', 'N/A')}</strong> ({p.get('year', 'N/A')})<br>
                    <span style="color: #555; font-size: 0.9rem;">{p.get('conflict', '')}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("No conflicting evidence found")

    # Research Gaps
    gaps = citations.get('research_gaps', [])
    if gaps:
        st.markdown("#### Research Gaps")
        for gap in gaps:
            st.markdown(f"- {gap}")

    # Citation Context
    context = citations.get('citation_context', '')
    if context:
        st.markdown("#### Citation Context")
        st.markdown(context)


def render_plagiarism_tab(plagiarism):
    """Render Agent 4 results"""
    score = plagiarism.get('plagiarism_risk_score', 0)
    level = plagiarism.get('risk_level', 'unknown')

    col1, col2 = st.columns([1, 2])
    with col1:
        # Risk gauge
        color = "#2e7d32" if score < 30 else ("#f57f17" if score < 60 else "#c62828")
        st.markdown(f"""
        <div style="text-align: center; padding: 1.5rem;">
            <div style="font-size: 3rem; font-weight: 700; color: {color};">{score}/100</div>
            <div>{get_badge(level, invert=True)}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"**Overall Assessment:**")
        st.markdown(plagiarism.get('overall_assessment', 'N/A'))

    # Missing Citations
    missing = plagiarism.get('missing_citations', [])
    if missing:
        st.markdown(f"#### Missing Citations ({len(missing)})")
        for i, mc in enumerate(missing):
            severity = mc.get('severity', 'low')
            icon = "🟢" if severity == "low" else ("🟡" if severity == "medium" else "🔴")
            with st.expander(f"{icon} {mc.get('text', 'N/A')[:80]}..."):
                st.markdown(f"**Reason:** {mc.get('reason', 'N/A')}")
                st.markdown(f"**Severity:** {severity.upper()}")

    # Suspicious Sections
    suspicious = plagiarism.get('suspicious_sections', [])
    if suspicious:
        st.markdown(f"#### Suspicious Sections ({len(suspicious)})")
        for i, s in enumerate(suspicious):
            with st.expander(f"Section {i+1}: {s.get('issue', 'N/A')[:60]}..."):
                st.markdown(f'> "{s.get("text", "N/A")[:200]}..."')
                st.markdown(f"**Recommendation:** {s.get('recommendation', 'N/A')}")

    # Recommendations
    recs = plagiarism.get('recommendations', [])
    if recs:
        st.markdown("#### Recommendations")
        for rec in recs:
            st.markdown(f"- {rec}")


def render_journals_tab(journals):
    """Render Agent 5 results"""
    queries = journals.get('search_queries_used', [])
    if queries:
        st.markdown(f"**Search Queries:** {', '.join(queries)}")
    st.markdown(f"**Journals Analyzed:** {journals.get('journals_found', 0)}")
    confidence = journals.get('recommendation_confidence', 'unknown')
    st.markdown(f"**Confidence:** {get_badge(confidence)}", unsafe_allow_html=True)

    # Primary Recommendations
    primary = journals.get('primary_recommendations', [])
    if primary:
        st.markdown("#### Primary Recommendations (Best Fit)")
        for j in primary:
            oa = "Open Access" if j.get('is_open_access') else "Subscription"
            apc = f"${j['apc_usd']}" if j.get('apc_usd') else "N/A"
            impact = j.get('impact_factor_2yr')
            impact_text = f"{impact:.2f}" if isinstance(impact, (int, float)) and impact is not None else "N/A"
            scope = j.get('scope_fit', 'N/A')
            acceptance = j.get('acceptance_likelihood', 'N/A')

            st.markdown(f"""
            <div class="journal-card">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <strong style="font-size: 1.1rem; color: #2e7d32;">{j.get('journal_name', 'Unknown')}</strong><br>
                        <span style="color: #666;">{j.get('publisher', 'Unknown')}</span>
                    </div>
                    <div style="text-align: right;">
                        {get_badge(scope)} {get_badge(acceptance)}
                    </div>
                </div>
                <div style="margin-top: 0.8rem; display: flex; gap: 1.5rem; flex-wrap: wrap;">
                    <span>📊 <strong>Citedness:</strong> {impact_text}</span>
                    <span>📈 <strong>H-Index:</strong> {j.get('h_index', 'N/A')}</span>
                    <span>📖 <strong>{oa}</strong></span>
                    <span>💰 <strong>APC:</strong> {apc}</span>
                </div>
                <div style="margin-top: 0.6rem; color: #555; font-size: 0.9rem;">
                    {j.get('fit_reasoning', '')}
                </div>
                {"<div style='margin-top: 0.4rem;'><a href='" + j['homepage_url'] + "' target='_blank' style='color: #2e7d32;'>🔗 Journal Homepage</a></div>" if j.get('homepage_url') else ""}
            </div>
            """, unsafe_allow_html=True)

    # Secondary Recommendations
    secondary = journals.get('secondary_recommendations', [])
    if secondary:
        st.markdown("#### Secondary Recommendations (Backup)")
        for j in secondary:
            oa = "Open Access" if j.get('is_open_access') else "Subscription"
            apc = f"${j['apc_usd']}" if j.get('apc_usd') else "N/A"
            impact = j.get('impact_factor_2yr')
            impact_text = f"{impact:.2f}" if isinstance(impact, (int, float)) and impact is not None else "N/A"

            st.markdown(f"""
            <div class="journal-card secondary">
                <strong>{j.get('journal_name', 'Unknown')}</strong> — {j.get('publisher', 'Unknown')}<br>
                <span style="font-size: 0.9rem; color: #666;">
                    Citedness: {impact_text} | H-Index: {j.get('h_index', 'N/A')} | {oa} | APC: {apc}
                </span><br>
                <span style="font-size: 0.9rem; color: #555;">{j.get('fit_reasoning', '')}</span>
            </div>
            """, unsafe_allow_html=True)

    # Publication Strategy
    strategy = journals.get('publication_strategy', '')
    if strategy:
        st.markdown("#### Publication Strategy")
        st.info(strategy)

    # Strengths & Concerns
    col1, col2 = st.columns(2)
    with col1:
        strengths = journals.get('key_strengths_for_submission', [])
        if strengths:
            st.markdown("#### Strengths for Submission")
            for s in strengths:
                st.success(s)
    with col2:
        concerns = journals.get('potential_concerns_for_reviewers', [])
        if concerns:
            st.markdown("#### Potential Concerns")
            for c in concerns:
                st.warning(c)


def render_dataviz_tab(visualization):
    """Render Agent 7 results"""
    quality = visualization.get('overall_quality', 'N/A')
    figures_count = visualization.get('figures_analyzed', 0)

    col1, col2 = st.columns([1, 2])
    with col1:
        color = get_score_color(quality)
        quality_display = f"{quality}/5" if quality != "N/A" else "N/A"
        st.markdown(f"""
        <div style="text-align: center; padding: 1.5rem;">
            <div style="font-size: 3rem; font-weight: 700; color: {color};">{quality_display}</div>
            <div style="font-size: 0.9rem; color: #666;">Overall Visualization Quality</div>
            <div style="margin-top: 0.5rem; font-size: 1.1rem;">{figures_count} figures analyzed</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("**Overall Assessment:**")
        st.markdown(visualization.get('overall_assessment', 'N/A'))

    # Caption analysis summary
    cap = visualization.get('caption_analysis', {})
    if cap.get('references_found', 0) > 0:
        ref_quality = cap.get('reference_quality', 'unknown')
        st.markdown(f"**Figure References Found:** {cap['references_found']} — Reference Quality: {get_badge(ref_quality.upper() if ref_quality != 'unknown' else 'UNKNOWN')}", unsafe_allow_html=True)
        if cap.get('orphan_figures'):
            st.warning(f"Orphan figures (not referenced in text): {', '.join(cap['orphan_figures'])}")
        if cap.get('dangling_references'):
            st.warning(f"Dangling references (referenced but not found): {', '.join(cap['dangling_references'])}")

    # Limitations info
    st.info("Note: Vision-based analysis is approximate. Subtle details like small text or precise color measurements may be missed. Vector graphics may not always be extracted from PDFs.")

    # Per-figure analysis
    figures = visualization.get('figures', [])
    if figures:
        st.markdown("#### Per-Figure Analysis")
        for fig in figures:
            fig_num = fig.get('figure_number', '?')
            fig_score = fig.get('overall_figure_score', 'N/A')
            chart_type = fig.get('chart_type_detected', 'unknown')
            priority = fig.get('priority', 'minor')
            priority_label = priority.upper()

            with st.expander(f"Figure {fig_num} (p.{fig.get('page', '?')}) — {chart_type.title()} — Score: {fig_score}/5 — {priority_label}"):
                # Score grid
                score_cols = st.columns(5)
                score_items = [
                    ("Color", fig.get('color_assessment', {}).get('score')),
                    ("Axes", fig.get('axis_assessment', {}).get('score')),
                    ("Data-Ink", fig.get('data_ink_ratio', {}).get('score')),
                    ("Legend", fig.get('legend_assessment', {}).get('score')),
                    ("Caption", fig.get('caption_quality', {}).get('score')),
                ]
                for col, (label, score) in zip(score_cols, score_items):
                    with col:
                        if score is not None and isinstance(score, (int, float)):
                            sc = get_score_color(score)
                            st.markdown(f"<div style='text-align:center'><span style='font-size:1.3rem;font-weight:700;color:{sc}'>{score}/5</span><br><span style='font-size:0.8rem;color:#666'>{label}</span></div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div style='text-align:center'><span style='font-size:1.3rem;font-weight:700;color:#888'>N/A</span><br><span style='font-size:0.8rem;color:#666'>{label}</span></div>", unsafe_allow_html=True)

                # Chart type check
                appropriate = fig.get('chart_type_appropriate')
                if appropriate is not None:
                    icon = "✅" if appropriate else "❌"
                    st.markdown(f"**Chart Type:** {chart_type.title()} — {icon} {'Appropriate' if appropriate else 'Consider alternative'}")
                    if fig.get('chart_type_suggestion'):
                        st.markdown(f"  Suggestion: {fig['chart_type_suggestion']}")

                # Quick checks
                st.markdown("**Quick Checks:**")
                checks = []
                color_a = fig.get('color_assessment', {})
                if color_a.get('colorblind_friendly') is not None:
                    checks.append(("Colorblind friendly", color_a['colorblind_friendly']))
                axis_a = fig.get('axis_assessment', {})
                if axis_a.get('labels_clear') is not None:
                    checks.append(("Axis labels clear", axis_a['labels_clear']))
                if axis_a.get('scale_appropriate') is not None:
                    checks.append(("Scale appropriate", axis_a['scale_appropriate']))
                if axis_a.get('zero_baseline') is not None:
                    checks.append(("Zero baseline", axis_a['zero_baseline']))
                ink = fig.get('data_ink_ratio', {})
                if ink.get('chart_junk_present') is not None:
                    checks.append(("No chart junk", not ink['chart_junk_present']))
                if ink.get('unnecessary_3d') is not None:
                    checks.append(("No unnecessary 3D", not ink['unnecessary_3d']))
                stats_el = fig.get('statistical_elements', {})
                if stats_el.get('error_bars_present') is not None:
                    checks.append(("Error bars present", stats_el['error_bars_present']))
                if stats_el.get('sample_size_shown') is not None:
                    checks.append(("Sample size shown", stats_el['sample_size_shown']))
                if stats_el.get('significance_indicated') is not None:
                    checks.append(("Significance indicated", stats_el['significance_indicated']))

                for label, val in checks:
                    icon = "✅" if val else "❌"
                    st.markdown(f"- {icon} {label}")

                # Strengths & Improvements
                col_s, col_i = st.columns(2)
                with col_s:
                    strengths = fig.get('strengths', [])
                    if strengths:
                        st.markdown("**Strengths:**")
                        for s in strengths:
                            st.success(s)
                with col_i:
                    improvements = fig.get('improvements', [])
                    if improvements:
                        st.markdown("**Improvements:**")
                        for imp in improvements:
                            st.warning(imp)

                # Issues from sub-assessments
                all_issues = []
                for key in ['color_assessment', 'axis_assessment', 'data_ink_ratio', 'legend_assessment', 'statistical_elements', 'caption_quality']:
                    sub = fig.get(key, {})
                    all_issues.extend(sub.get('issues', []))
                    all_issues.extend(sub.get('suggestions', []))
                if all_issues:
                    st.markdown("**Detailed Issues & Suggestions:**")
                    for issue in all_issues:
                        if "failed" not in issue.lower():
                            st.markdown(f"- {issue}")

    # Common patterns
    patterns = visualization.get('common_patterns', [])
    if patterns:
        st.markdown("#### Common Patterns")
        for p in patterns:
            st.markdown(f"- {p}")

    # Best practice violations
    violations = visualization.get('best_practice_violations', [])
    if violations:
        st.markdown("#### Best Practice Violations")
        for v in violations:
            st.warning(v)

    # Strengths
    strengths_list = visualization.get('strengths', [])
    if strengths_list:
        st.markdown("#### Strengths")
        for s in strengths_list:
            st.success(s)

    # Recommendations
    recs = visualization.get('recommendations', [])
    if recs:
        st.markdown("#### Recommendations")
        for r in recs:
            st.markdown(f"- {r}")

    # Strategy
    strategy = visualization.get('visualization_strategy', '')
    if strategy:
        st.markdown("#### Visualization Strategy")
        st.info(strategy)


def render_writing_tab(writing):
    """Render Agent 8 results"""
    score = writing.get('overall_writing_score', 'N/A')
    readability = writing.get('readability_level', 'unknown')

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        color = get_score_color(score)
        score_display = f"{score}/5" if score != "N/A" else "N/A"
        st.markdown(f"""
        <div class="metric-card" style="min-height: 130px;">
            <div class="metric-value" style="font-size: 2.5rem; color: {color};">{score_display}</div>
            <div class="metric-label">Writing Quality</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card" style="min-height: 130px;">
            <div class="metric-value" style="font-size: 1.2rem;">{get_badge(readability.upper())}</div>
            <div class="metric-label">Readability Level</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("**Overall Assessment:**")
        st.markdown(writing.get('overall_assessment', 'N/A'))

    # Quantitative Metrics
    metrics = writing.get('quantitative_metrics', {})
    if metrics and metrics.get('total_words', 0) > 0:
        st.markdown("#### Quantitative Metrics")
        m_cols = st.columns(4)
        with m_cols[0]:
            avg_sl = metrics.get('avg_sentence_length', 0)
            sl_color = "#2e7d32" if 15 <= avg_sl <= 25 else ("#f57f17" if avg_sl <= 30 else "#c62828")
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="font-size: 1.4rem; color: {sl_color};">{avg_sl}</div>
                <div class="metric-label">Avg Sentence Length</div>
                <div style="font-size: 0.75rem; color: #999;">Target: 15-25 words</div>
            </div>
            """, unsafe_allow_html=True)
        with m_cols[1]:
            pv = metrics.get('passive_voice_ratio', 0)
            pv_color = "#2e7d32" if pv < 0.25 else ("#f57f17" if pv < 0.35 else "#c62828")
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="font-size: 1.4rem; color: {pv_color};">{pv:.0%}</div>
                <div class="metric-label">Passive Voice</div>
                <div style="font-size: 0.75rem; color: #999;">Target: &lt;25%</div>
            </div>
            """, unsafe_allow_html=True)
        with m_cols[2]:
            hedge = metrics.get('hedge_word_count', 0)
            filler = metrics.get('filler_word_count', 0)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="font-size: 1.4rem; color: {'#f57f17' if hedge > 15 else '#2e7d32'};">{hedge}</div>
                <div class="metric-label">Hedge Words</div>
                <div style="font-size: 0.75rem; color: #999;">Filler: {filler}</div>
            </div>
            """, unsafe_allow_html=True)
        with m_cols[3]:
            uwr = metrics.get('unique_word_ratio', 0)
            trans = metrics.get('transition_word_count', 0)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="font-size: 1.4rem; color: {'#2e7d32' if uwr > 0.40 else '#f57f17'};">{uwr:.0%}</div>
                <div class="metric-label">Vocabulary Diversity</div>
                <div style="font-size: 0.75rem; color: #999;">Transitions: {trans}</div>
            </div>
            """, unsafe_allow_html=True)

    # Section-by-section analysis
    section_analyses = writing.get('sections', {})
    if section_analyses:
        st.markdown("#### Section-by-Section Analysis")
        for sec_name, sec_data in section_analyses.items():
            sec_score = sec_data.get('overall_section_score', 'N/A')
            with st.expander(f"{sec_name.title()} — Score: {sec_score}/5"):
                # Score grid
                score_cols = st.columns(6)
                score_items = [
                    ("Clarity", sec_data.get('clarity')),
                    ("Conciseness", sec_data.get('conciseness')),
                    ("Tone", sec_data.get('academic_tone')),
                    ("Structure", sec_data.get('structure')),
                    ("Precision", sec_data.get('precision')),
                    ("Section-Specific", sec_data.get('section_specific')),
                ]
                for col, (label, s) in zip(score_cols, score_items):
                    with col:
                        if s is not None and isinstance(s, (int, float)):
                            sc = get_score_color(s)
                            st.markdown(f"<div style='text-align:center'><span style='font-size:1.3rem;font-weight:700;color:{sc}'>{s}/5</span><br><span style='font-size:0.75rem;color:#666'>{label}</span></div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div style='text-align:center'><span style='font-size:1.3rem;font-weight:700;color:#888'>N/A</span><br><span style='font-size:0.75rem;color:#666'>{label}</span></div>", unsafe_allow_html=True)

                # Strengths & Weaknesses
                col_s, col_w = st.columns(2)
                with col_s:
                    strengths = sec_data.get('strengths', [])
                    if strengths:
                        st.markdown("**Strengths:**")
                        for s in strengths:
                            st.success(s)
                with col_w:
                    weaknesses = sec_data.get('weaknesses', [])
                    if weaknesses:
                        st.markdown("**Weaknesses:**")
                        for w in weaknesses:
                            st.warning(w)

                # Suggestions
                suggestions = sec_data.get('suggestions', [])
                if suggestions:
                    st.markdown("**Suggestions:**")
                    for sug in suggestions:
                        st.markdown(f"- {sug}")

                # Problematic sentences
                prob_sentences = sec_data.get('problematic_sentences', [])
                if prob_sentences:
                    st.markdown("**Problematic Sentences:**")
                    for ps in prob_sentences:
                        st.markdown(f"""
                        <div style="background: #fff8e1; padding: 0.8rem; border-radius: 8px; margin: 0.4rem 0; border-left: 3px solid #ffa000;">
                            <div style="color: #c62828; font-size: 0.85rem;"><strong>Issue:</strong> {ps.get('issue', 'N/A')}</div>
                            <div style="color: #555; font-size: 0.85rem; margin-top: 0.3rem;"><strong>Original:</strong> "{ps.get('text', 'N/A')}"</div>
                            <div style="color: #2e7d32; font-size: 0.85rem; margin-top: 0.3rem;"><strong>Suggestion:</strong> {ps.get('suggestion', 'N/A')}</div>
                        </div>
                        """, unsafe_allow_html=True)

    # Cross-section patterns
    patterns = writing.get('cross_section_patterns', [])
    if patterns:
        st.markdown("#### Cross-Section Patterns")
        for p in patterns:
            st.markdown(f"- {p}")

    # Top improvements
    improvements = writing.get('top_improvements', [])
    if improvements:
        st.markdown("#### Top Improvements")
        for imp in improvements:
            priority = imp.get('priority', '?')
            badge_color = "#c62828" if priority == 1 else ("#f57f17" if priority == 2 else "#ff8f00")
            st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 8px; margin: 0.4rem 0; border-left: 4px solid {badge_color}; box-shadow: 0 1px 4px rgba(0,0,0,0.06);">
                <span style="background: {badge_color}; color: white; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.8rem; font-weight: 700;">#{priority}</span>
                <strong style="margin-left: 0.5rem;">{imp.get('issue', 'N/A')}</strong>
                <div style="color: #555; font-size: 0.9rem; margin-top: 0.4rem;">{imp.get('detail', '')}</div>
            </div>
            """, unsafe_allow_html=True)

    # Style guide references
    refs = writing.get('style_guide_references', [])
    if refs:
        st.markdown("#### Style Guide References")
        for ref in refs:
            st.markdown(f"- {ref}")


def render_funding_tab(funding):
    """Render Agent 6 results"""
    confidence = funding.get('data_confidence', 'unknown')
    st.markdown(f"**Data Confidence:** {get_badge(confidence)}", unsafe_allow_html=True)
    st.markdown(f"**Funded Papers Analyzed:** {funding.get('total_similar_funded_papers', 0)}")
    st.markdown(f"**Funders Found:** {funding.get('funders_found', 0)}")

    queries = funding.get('search_queries_used', [])
    if queries:
        st.markdown(f"**Search Queries:** {', '.join(queries)}")

    # Funding Landscape
    landscape = funding.get('funding_landscape', '')
    if landscape:
        st.markdown("#### Funding Landscape")
        st.info(landscape)

    # Primary Funders
    primary = funding.get('primary_funders', [])
    if primary:
        st.markdown("#### Primary Funding Sources (Best Fit)")
        for f in primary:
            relevance = f.get('relevance', 'medium')
            programs = f.get('known_programs', [])
            programs_text = ', '.join(programs) if programs else 'N/A'

            st.markdown(f"""
            <div class="journal-card">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <strong style="font-size: 1.1rem; color: #2e7d32;">{f.get('funder_name', 'Unknown')}</strong>
                        <span style="color: #888; margin-left: 0.5rem;">{f.get('country', '?')}</span>
                    </div>
                    <div>{get_badge(relevance)}</div>
                </div>
                <div style="margin-top: 0.6rem; color: #555; font-size: 0.9rem;">
                    {f.get('relevance_reasoning', '')}
                </div>
                <div style="margin-top: 0.8rem; display: flex; gap: 1.5rem; flex-wrap: wrap;">
                    <span>💰 <strong>{f.get('typical_amount', 'N/A')}</strong></span>
                    <span>📅 <strong>{f.get('typical_duration', 'N/A')}</strong></span>
                </div>
                <div style="margin-top: 0.5rem;">
                    <strong>Programs:</strong> {programs_text}
                </div>
                <div style="margin-top: 0.4rem; font-size: 0.85rem; color: #666;">
                    <strong>Eligibility:</strong> {f.get('eligibility_notes', 'N/A')}
                </div>
                <div style="margin-top: 0.4rem; font-size: 0.85rem; color: #2e7d32;">
                    💡 <strong>Tip:</strong> {f.get('application_tip', 'N/A')}
                </div>
                {"<div style='margin-top: 0.4rem;'><a href='" + f['homepage_url'] + "' target='_blank' style='color: #2e7d32;'>🔗 Funder Homepage</a></div>" if f.get('homepage_url') else ""}
            </div>
            """, unsafe_allow_html=True)

    # Secondary Funders
    secondary = funding.get('secondary_funders', [])
    if secondary:
        st.markdown("#### Secondary Funding Sources (Additional Options)")
        for f in secondary:
            programs = f.get('known_programs', [])
            programs_text = ', '.join(programs) if programs else 'N/A'

            st.markdown(f"""
            <div class="journal-card secondary">
                <strong>{f.get('funder_name', 'Unknown')}</strong> ({f.get('country', '?')})
                — {get_badge(f.get('relevance', 'low'))}<br>
                <span style="font-size: 0.9rem; color: #666;">
                    Amount: {f.get('typical_amount', 'N/A')} | Duration: {f.get('typical_duration', 'N/A')} | Programs: {programs_text}
                </span><br>
                <span style="font-size: 0.9rem; color: #555;">{f.get('relevance_reasoning', '')}</span>
            </div>
            """, unsafe_allow_html=True)

    # Funding Strategy
    strategy = funding.get('funding_strategy', '')
    if strategy:
        st.markdown("#### Funding Strategy")
        st.info(strategy)


def run_analysis(pdf_path, selected_agents):
    """Run the analysis workflow, only running selected agents"""
    from workflow import PaperAnalyzerWorkflow

    workflow = PaperAnalyzerWorkflow()

    # Step 1: Extract text
    full_text = workflow.extract_text_from_pdf(pdf_path)
    yield {"step": "pdf_extracted", "chars": len(full_text)}

    # Step 2: Extract sections
    sections, paper_type = workflow.extract_sections(full_text)
    is_review = paper_type in ("review", "meta_analysis")
    yield {"step": "sections_extracted", "paper_type": paper_type, "sections": sections}

    # Results Synthesizer
    if "results" in selected_agents:
        if sections.get('results'):
            results_analysis = workflow.results_synthesizer.analyze(sections['results'])
        elif sections.get('discussion'):
            results_analysis = workflow.results_synthesizer.analyze(sections['discussion'])
        else:
            results_analysis = workflow._empty_results_analysis()
    else:
        results_analysis = _skipped_data("results")
    yield {"step": "agent2_done", "data": results_analysis}

    # Writing Coach
    if "writing" in selected_agents:
        writing_analysis = workflow.writing_coach.analyze(sections, paper_type)
    else:
        writing_analysis = _skipped_data("writing")
    yield {"step": "agent8_done", "data": writing_analysis}

    # Methodology Critic
    if "methodology" in selected_agents:
        if is_review:
            methods_analysis = workflow._review_methods_analysis()
        elif sections.get('methods'):
            methods_analysis = workflow.methodology_critic.analyze(
                sections['methods'],
                abstract=sections.get('abstract', ''),
                results_text=sections.get('results', '')
            )
        else:
            methods_analysis = workflow._empty_methods_analysis()
    else:
        methods_analysis = _skipped_data("methodology")
    yield {"step": "agent1_done", "data": methods_analysis}

    # DataViz Critic
    if "visualization" in selected_agents:
        visualization_analysis = workflow.visualization_critic.analyze(
            pdf_path, full_text, sections.get('results', '')
        )
    else:
        visualization_analysis = _skipped_data("visualization")
    yield {"step": "agent7_done", "data": visualization_analysis}

    # Agent 3 - Citations
    if "citations" in selected_agents:
        citation_analysis = workflow.citation_hunter.analyze(
            sections.get('title', 'Unknown Title'),
            sections.get('abstract', '')
        )
    else:
        citation_analysis = _skipped_data("citations")
    yield {"step": "agent3_done", "data": citation_analysis}

    # Agent 4 - Plagiarism
    if "plagiarism" in selected_agents:
        plagiarism_analysis = workflow.plagiarism_detector.analyze(full_text, paper_type)
    else:
        plagiarism_analysis = _skipped_data("plagiarism")
    yield {"step": "agent4_done", "data": plagiarism_analysis}

    # Agent 5 - Journals
    if "journals" in selected_agents:
        methods_quality_score = methods_analysis.get('overall_quality')
        evidence_strength_val = results_analysis.get('strength_of_evidence', '')
        journal_recommendations = workflow.journal_recommender.analyze(
            sections.get('title', 'Unknown Title'),
            sections.get('abstract', ''),
            paper_type=paper_type,
            methods_quality=methods_quality_score if methods_quality_score != "N/A" else None,
            evidence_strength=evidence_strength_val if evidence_strength_val != "unknown" else None
        )
    else:
        journal_recommendations = _skipped_data("journals")
    yield {"step": "agent5_done", "data": journal_recommendations}

    # Agent 6 - Funding
    if "funding" in selected_agents:
        funding_recommendations = workflow.funding_advisor.analyze(
            sections.get('title', 'Unknown Title'),
            sections.get('abstract', ''),
            paper_type=paper_type
        )
    else:
        funding_recommendations = _skipped_data("funding")
    yield {"step": "agent6_done", "data": funding_recommendations}

    # Generate markdown report
    report = workflow.generate_report(
        sections, methods_analysis, results_analysis,
        visualization_analysis, writing_analysis,
        citation_analysis, plagiarism_analysis, journal_recommendations,
        funding_recommendations, paper_type
    )
    yield {
        "step": "complete",
        "report": report,
        "sections": sections,
        "paper_type": paper_type,
        "methods": methods_analysis,
        "results": results_analysis,
        "visualization": visualization_analysis,
        "writing": writing_analysis,
        "citations": citation_analysis,
        "plagiarism": plagiarism_analysis,
        "journals": journal_recommendations,
        "funding": funding_recommendations,
        "selected_agents": selected_agents
    }


# --- Main App ---

render_header()
render_sidebar()

# Initialize session state
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "analyzing" not in st.session_state:
    st.session_state.analyzing = False

# Action bar (above file uploader, visible when results exist)
if st.session_state.analysis_result is not None:
    _r = st.session_state.analysis_result
    _report_md = _r['report']
    _title = _r['sections'].get('title', 'Unknown Title')
    _paper_type = _r['paper_type']

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        st.download_button(
            "Download Report (Markdown)",
            data=_report_md,
            file_name=f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True
        )
    with col2:
        _json_data = json.dumps({
            "paper_type": _paper_type,
            "title": _title,
            "results": _r.get('results'),
            "writing": _r.get('writing'),
            "methodology": _r.get('methods'),
            "visualization": _r.get('visualization'),
            "citations": _r.get('citations'),
            "plagiarism": _r.get('plagiarism'),
            "journals": _r.get('journals'),
            "funding": _r.get('funding')
        }, indent=2, ensure_ascii=False)
        # Auto-save JSON to data/output/
        _json_output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "output")
        os.makedirs(_json_output_dir, exist_ok=True)
        _json_filename = os.path.join(_json_output_dir, f"analysis_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        if not os.path.exists(_json_filename):
            with open(_json_filename, "w", encoding="utf-8") as _jf:
                _jf.write(_json_data)
        st.download_button(
            "Download Data (JSON)",
            data=_json_data,
            file_name=os.path.basename(_json_filename),
            mime="application/json",
            use_container_width=True
        )
    with col3:
        if st.button("Analyze Another Paper", use_container_width=True):
            st.session_state.analysis_result = None
            st.rerun()
    st.markdown("---")

# Upload area
uploaded_file = st.file_uploader(
    "Upload your research paper (PDF)",
    type=["pdf"],
    help="Supported: Original Research, Reviews, Meta-Analyses, Case Studies"
)

if uploaded_file is not None and st.session_state.analysis_result is None:
    st.markdown(f"**Uploaded:** {uploaded_file.name} ({uploaded_file.size / 1024:.0f} KB)")

    # Get selected agents from sidebar
    selected_agents = st.session_state.get("selected_agents", ALL_AGENT_KEYS)
    n_sel = len(selected_agents)
    if n_sel < 8:
        st.caption(f"Running {n_sel} of 8 agents")

    if st.button("Analyze Paper", use_container_width=True):
        if not selected_agents:
            st.error("Please select at least one agent in the sidebar.")
        else:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            try:
                # Progress container
                progress_container = st.container()

                with progress_container:
                    # Build dynamic steps list based on selected agents
                    steps = [
                        ("Extracting PDF text...", "📄"),
                        ("Identifying paper sections & type...", "✂️"),
                    ]
                    # Map step_name → step index (built dynamically)
                    step_map = {"pdf_extracted": 1, "sections_extracted": 2}

                    agent_steps = [
                        ("results", "agent2_done", "Results Synthesizer: Synthesizing results...", "📊"),
                        ("writing", "agent8_done", "Writing Coach: Evaluating writing quality...", "✍️"),
                        ("methodology", "agent1_done", "Methodology Critic: Analyzing methodology...", "🔬"),
                        ("visualization", "agent7_done", "DataViz Critic: Analyzing data visualizations...", "📈"),
                        ("citations", "agent3_done", "Citation Hunter: Searching related literature...", "🔗"),
                        ("plagiarism", "agent4_done", "Plagiarism Detector: Checking integrity...", "🚨"),
                        ("journals", "agent5_done", "Journal Recommender: Recommending journals...", "📚"),
                        ("funding", "agent6_done", "Funding Advisor: Searching funding sources...", "💰"),
                    ]
                    for agent_key, step_name, label, icon in agent_steps:
                        if agent_key in selected_agents:
                            steps.append((label, icon))
                            step_map[step_name] = len(steps) - 1

                    steps.append(("Generating report...", "📝"))
                    total_steps = len(steps)

                    progress_bar = st.progress(0, text="Starting analysis...")
                    status_text = st.empty()
                    log_expander = st.expander("Live Log Output", expanded=False)
                    log_area = log_expander.empty()

                    current_step = 0
                    log_lines = []

                    # Capture stdout for live log
                    old_stdout = sys.stdout
                    old_stderr = sys.stderr
                    log_buffer = io.StringIO()

                    class TeeOutput:
                        def __init__(self, buffer, original):
                            self.buffer = buffer
                            self.original = original
                        def write(self, text):
                            self.buffer.write(text)
                            self.original.write(text)
                        def flush(self):
                            self.buffer.flush()
                            self.original.flush()

                    sys.stdout = TeeOutput(log_buffer, old_stdout)
                    sys.stderr = TeeOutput(log_buffer, old_stderr)

                    try:
                        final_result = None
                        for update in run_analysis(tmp_path, selected_agents):
                            step_name = update["step"]

                            if step_name == "complete":
                                progress_bar.progress(1.0, text="Analysis complete!")
                                status_text.markdown("**Analysis complete!**")
                                final_result = update
                            elif step_name in step_map:
                                idx = step_map[step_name]
                                current_step = idx
                                if step_name == "sections_extracted":
                                    pt = update['paper_type'].replace('_', ' ').title()
                                    status_text.markdown(f"**Paper Type: {pt}** — {steps[idx][1]} {steps[idx][0]}")
                                else:
                                    status_text.markdown(f"**{steps[idx][1]} {steps[idx][0]}**")
                                progress_bar.progress(idx / total_steps, text=steps[idx][0])

                            # Update log
                            current_log = log_buffer.getvalue()
                            if current_log:
                                log_area.code(current_log[-3000:], language="")

                        if final_result:
                            st.session_state.analysis_result = final_result
                            st.rerun()

                    finally:
                        sys.stdout = old_stdout
                        sys.stderr = old_stderr

            finally:
                # Clean up temp file
                try:
                    os.unlink(tmp_path)
                except:
                    pass

# --- Display Results ---
if st.session_state.analysis_result is not None:
    result = st.session_state.analysis_result

    sections = result['sections']
    paper_type = result['paper_type']
    methods = result['methods']
    results_data = result['results']
    visualization = result['visualization']
    writing = result['writing']
    citations = result['citations']
    plagiarism = result['plagiarism']
    journals = result['journals']
    funding = result['funding']
    report_md = result['report']

    # Paper info
    title = sections.get('title', 'Unknown Title')
    st.markdown(f"### {title}")
    st.markdown(f"**Paper Type:** {paper_type.replace('_', ' ').title()}")

    # Summary metrics
    st.markdown("---")
    render_summary_metrics(methods, results_data, plagiarism, journals, visualization, writing)
    st.markdown("---")

    # Tabs for each agent
    _skipped_msg = "This agent was not selected for this analysis. Select it in the sidebar and re-analyze."
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "📊 Results",
        "✍️ Writing",
        "🔬 Methodology",
        "📈 DataViz",
        "🔗 Citations",
        "🚨 Plagiarism",
        "📚 Journals",
        "💰 Funding",
        "📄 Full Report"
    ])

    with tab1:
        if results_data.get('_skipped'):
            st.info(f"📊 **Results Synthesizer** — {_skipped_msg}")
        else:
            render_results_tab(results_data)

    with tab2:
        if writing.get('_skipped'):
            st.info(f"✍️ **Writing Coach** — {_skipped_msg}")
        else:
            render_writing_tab(writing)

    with tab3:
        if methods.get('_skipped'):
            st.info(f"🔬 **Methodology Critic** — {_skipped_msg}")
        else:
            render_methodology_tab(methods)

    with tab4:
        if visualization.get('_skipped'):
            st.info(f"📈 **DataViz Critic** — {_skipped_msg}")
        else:
            render_dataviz_tab(visualization)

    with tab5:
        if citations.get('_skipped'):
            st.info(f"🔗 **Citation Hunter** — {_skipped_msg}")
        else:
            render_citations_tab(citations)

    with tab6:
        if plagiarism.get('_skipped'):
            st.info(f"🚨 **Plagiarism Detector** — {_skipped_msg}")
        else:
            render_plagiarism_tab(plagiarism)

    with tab7:
        if journals.get('_skipped'):
            st.info(f"📚 **Journal Recommender** — {_skipped_msg}")
        else:
            render_journals_tab(journals)

    with tab8:
        if funding.get('_skipped'):
            st.info(f"💰 **Funding Advisor** — {_skipped_msg}")
        else:
            render_funding_tab(funding)

    with tab9:
        st.markdown(report_md)

elif uploaded_file is None:
    # Welcome state - show example/info
    st.markdown("")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="agent-card" style="text-align: center;">
            <div style="font-size: 2.5rem;">📄</div>
            <h4 style="color: #2e7d32;">1. Upload</h4>
            <p style="color: #666;">Drop your research paper PDF above</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="agent-card" style="text-align: center;">
            <div style="font-size: 2.5rem;">🤖</div>
            <h4 style="color: #2e7d32;">2. Analyze</h4>
            <p style="color: #666;">8 AI agents examine your paper in depth</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="agent-card" style="text-align: center;">
            <div style="font-size: 2.5rem;">📊</div>
            <h4 style="color: #2e7d32;">3. Results</h4>
            <p style="color: #666;">Get actionable feedback & journal recommendations</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")
    st.markdown("""
    <div style="text-align: center; color: #888; padding: 2rem;">
        <p style="font-size: 1.1rem;">Upload a PDF to get started</p>
    </div>
    """, unsafe_allow_html=True)
