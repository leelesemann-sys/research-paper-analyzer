from openai import AzureOpenAI
from agents.methodology import MethodologyCritic
from agents.results import ResultsSynthesizer
from agents.citations import CitationHunter
from agents.plagiarism import PlagiarismDetector
from agents.journals import JournalRecommender
from agents.funding import FundingAdvisor
from agents.visualization import DataVisualizationCritic
from agents.writing import WritingQualityCoach
from pypdf import PdfReader
from dotenv import load_dotenv
import os
import json
from datetime import datetime

load_dotenv()


class PaperAnalyzerWorkflow:
    """Orchestrates all 8 agents to analyze research papers"""

    def __init__(self):
        self.client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION")
        )
        self.methodology_critic = MethodologyCritic()
        self.results_synthesizer = ResultsSynthesizer()
        self.citation_hunter = CitationHunter()
        self.plagiarism_detector = PlagiarismDetector()
        self.journal_recommender = JournalRecommender()
        self.funding_advisor = FundingAdvisor()
        self.visualization_critic = DataVisualizationCritic()
        self.writing_coach = WritingQualityCoach()
        self.model = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF"""
        print(f"📄 Extracting text from: {pdf_path}\n")
        
        reader = PdfReader(pdf_path)
        full_text = ""
        
        for page in reader.pages:
            full_text += page.extract_text()
        
        print(f"✅ Extracted {len(full_text)} characters from {len(reader.pages)} pages\n")
        return full_text
    
    def extract_sections(self, full_text):
        """Extract paper sections and paper type using LLM"""
        print("✂️  Extracting paper sections via LLM...\n")

        try:
            result = self._extract_sections_llm(full_text)
        except Exception as e:
            print(f"❌ LLM section extraction failed: {e}")
            print("⚠️  Returning empty sections\n")
            result = {}

        # Extract paper_type separately
        paper_type = result.pop("paper_type", "original_research")

        # Fill missing sections with empty strings
        for section in ['title', 'abstract', 'introduction', 'methods', 'results', 'discussion', 'conclusion']:
            if section not in result:
                result[section] = ""

        print(f"📋 Paper type: {paper_type.upper().replace('_', ' ')}")
        print("✅ Sections extracted:")
        for section in ['title', 'abstract', 'introduction', 'methods', 'results', 'discussion', 'conclusion']:
            length = len(result.get(section, ''))
            status = "✅" if length > 100 else ("⚠️ " if length == 0 else "✅")
            print(f"   {status} {section.title()}: {length} chars")
        print()

        return result, paper_type

    def _extract_sections_llm(self, full_text):
        """Extract sections and paper type using GPT-4o"""

        system_prompt = """You are an expert at parsing scientific research papers.

Given the raw text extracted from a PDF, do TWO things:

1. Classify the paper type as one of:
   - "original_research" (has own methodology, experiments, data collection)
   - "review" (literature review, survey, synthesis of existing research)
   - "meta_analysis" (statistical synthesis of multiple studies)
   - "case_study" (detailed analysis of a specific case)
   - "other"

2. Identify and extract the paper sections. Map each to the closest standard category:
   - title: The paper title
   - abstract: Abstract/Summary
   - introduction: Introduction/Background
   - methods: Methodology/Methods/Experimental Design/Materials and Methods
   - results: Results/Experimental Results/Findings (if combined with Discussion, include full text here too)
   - discussion: Discussion/Interpretation (if combined with Results, include full text here too)
   - conclusion: Conclusion/Summary/Concluding Remarks

Return the COMPLETE text of each section, not a summary.
If a section like "Results and Discussion" combines two categories, assign the full text to BOTH "results" and "discussion".
For sections not present in the paper, return an empty string "".

Return JSON only:
{
  "paper_type": "original_research|review|meta_analysis|case_study|other",
  "title": "...",
  "abstract": "...",
  "introduction": "...",
  "methods": "...",
  "results": "...",
  "discussion": "...",
  "conclusion": "..."
}"""

        # Send up to 60k chars (enough for ~25 page papers, within GPT-4o's 128k context)
        text_to_analyze = full_text[:60000]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Extract sections from this paper:\n\n{text_to_analyze}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )

        return json.loads(response.choices[0].message.content)
    
    def run(self, pdf_path):
        """Run complete analysis workflow"""
        
        print("="*60)
        print("🔬 RESEARCH PAPER ANALYZER")
        print("="*60)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Step 1: Extract text
        full_text = self.extract_text_from_pdf(pdf_path)
        
        # Step 2: Extract sections + paper type
        sections, paper_type = self.extract_sections(full_text)
        is_review = paper_type in ("review", "meta_analysis")

        # Check if we have enough sections (skip for reviews)
        if not is_review:
            critical_sections = ['methods', 'results']
            missing = [s for s in critical_sections if not sections.get(s)]
            if missing:
                print(f"⚠️  WARNING: Missing sections: {', '.join(missing)}")
                print("⚠️  Analysis will continue but may be incomplete\n")

        # Step 3: Agent 1 - Methodology Analysis
        print("-"*60)
        if is_review:
            print("ℹ️  Skipping Agent 1 (paper is a review/meta-analysis - no own methodology expected)\n")
            methods_analysis = self._review_methods_analysis()
        elif sections.get('methods'):
            methods_analysis = self.methodology_critic.analyze(
                sections['methods'],
                abstract=sections.get('abstract', ''),
                results_text=sections.get('results', '')
            )
        else:
            print("⚠️  Skipping Agent 1 (no Methods section found)\n")
            methods_analysis = self._empty_methods_analysis()

        # Step 4: Agent 2 - Results Synthesis
        print("-"*60)
        if sections.get('results'):
            results_analysis = self.results_synthesizer.analyze(sections['results'])
        elif sections.get('discussion'):
            print("ℹ️  No separate Results section - using Discussion for synthesis\n")
            results_analysis = self.results_synthesizer.analyze(sections['discussion'])
        else:
            print("⚠️  Skipping Agent 2 (no Results section found)\n")
            results_analysis = self._empty_results_analysis()

        # Step 5: Agent 7 - Data Visualization Analysis
        print("-"*60)
        visualization_analysis = self.visualization_critic.analyze(
            pdf_path, full_text, sections.get('results', '')
        )

        # Step 6: Agent 8 - Writing Quality
        print("-"*60)
        writing_analysis = self.writing_coach.analyze(sections, paper_type)

        # Step 7: Agent 3 - Citation Analysis
        print("-"*60)
        citation_analysis = self.citation_hunter.analyze(
            sections.get('title', 'Unknown Title'),
            sections.get('abstract', '')
        )

        # Step 8: Agent 4 - Plagiarism Check
        print("-"*60)
        plagiarism_analysis = self.plagiarism_detector.analyze(full_text, paper_type)

        # Step 9: Agent 5 - Journal Recommendations
        print("-"*60)
        methods_quality_score = methods_analysis.get('overall_quality')
        evidence_strength_val = results_analysis.get('strength_of_evidence', '')

        journal_recommendations = self.journal_recommender.analyze(
            sections.get('title', 'Unknown Title'),
            sections.get('abstract', ''),
            paper_type=paper_type,
            methods_quality=methods_quality_score if methods_quality_score != "N/A" else None,
            evidence_strength=evidence_strength_val if evidence_strength_val != "unknown" else None
        )

        # Step 10: Agent 6 - Funding Recommendations
        print("-"*60)
        funding_recommendations = self.funding_advisor.analyze(
            sections.get('title', 'Unknown Title'),
            sections.get('abstract', ''),
            paper_type=paper_type
        )

        # Step 11: Generate Report
        print("-"*60)
        print("📝 Generating final report...\n")

        report = self.generate_report(
            sections,
            methods_analysis,
            results_analysis,
            visualization_analysis,
            writing_analysis,
            citation_analysis,
            plagiarism_analysis,
            journal_recommendations,
            funding_recommendations,
            paper_type
        )
        
        # Save report
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "output")
        os.makedirs(output_dir, exist_ok=True)
        report_filename = os.path.join(output_dir, f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
        with open(report_filename, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"✅ Report saved: {report_filename}")
        print("\n" + "="*60)
        print("✅ ANALYSIS COMPLETE!")
        print("="*60)
        
        return report
    
    def _review_methods_analysis(self):
        """Return structure for review/meta-analysis papers (no own methodology expected)"""
        return {
            "sample_size": {"n": "N/A", "adequate": True, "power_calculation": "N/A (review paper)", "comment": "Review paper - no own data collection"},
            "study_design": {"type": "literature review", "quality_score": "N/A", "appropriateness": "N/A (review paper)"},
            "statistical_methods": {"methods_used": [], "appropriate": True, "issues": []},
            "biases": {"identified": [], "addressed": True, "comment": "N/A (review paper)"},
            "reproducibility": {"score": "N/A", "comment": "N/A (review paper)"},
            "overall_quality": "N/A",
            "critical_issues": [],
            "strengths": []
        }

    def _empty_methods_analysis(self):
        """Return empty structure when methods not found"""
        return {
            "sample_size": {"n": 0, "adequate": False, "power_calculation": "not found", "comment": "Methods section not found"},
            "study_design": {"type": "unknown", "quality_score": 0, "appropriateness": "N/A"},
            "statistical_methods": {"methods_used": [], "appropriate": False, "issues": ["Methods section not found"]},
            "biases": {"identified": [], "addressed": False, "comment": "Cannot assess"},
            "reproducibility": {"score": 0, "comment": "Methods section not found"},
            "overall_quality": 0,
            "critical_issues": ["Methods section not found in paper"],
            "strengths": []
        }
    
    def _empty_results_analysis(self):
        """Return empty structure when results not found"""
        return {
            "primary_outcome": {"measure": "Not found", "result": "N/A", "statistically_significant": False, "p_value": "N/A"},
            "key_findings": [],
            "effect_sizes": [],
            "secondary_outcomes": [],
            "main_conclusion": "Results section not found",
            "strength_of_evidence": "unknown",
            "limitations_noted": ["Results section not found"]
        }
    
    def _format_journal_recommendations(self, recommendations):
        """Format a list of journal recommendations for the report"""
        if not recommendations:
            return "No recommendations available"

        lines = []
        for i, j in enumerate(recommendations):
            oa_status = "Open Access" if j.get('is_open_access') else "Subscription"
            apc_text = f"${j['apc_usd']}" if j.get('apc_usd') else "N/A"
            h_text = j.get('h_index', 'N/A')
            if2yr = j.get('impact_factor_2yr')
            if2yr_text = f"{if2yr:.2f}" if isinstance(if2yr, (int, float)) and if2yr is not None else "N/A"

            lines.append(f"""**{i+1}. {j.get('journal_name', 'Unknown')}**
- **Publisher:** {j.get('publisher', 'Unknown')}
- **2yr Mean Citedness:** {if2yr_text} | **H-Index:** {h_text}
- **Access:** {oa_status} | **APC:** {apc_text}
- **Scope Fit:** {j.get('scope_fit', 'N/A').upper()} | **Acceptance Likelihood:** {j.get('acceptance_likelihood', 'N/A').upper()}
- **Similar Papers Found:** {j.get('similar_papers_found', 0)}
- **Why:** {j.get('fit_reasoning', 'N/A')}
- **Homepage:** {j.get('homepage_url', 'N/A')}
""")
        return "\n".join(lines)

    def _format_funding_recommendations(self, funders):
        """Format a list of funding recommendations for the report"""
        if not funders:
            return "No recommendations available"

        lines = []
        for i, f in enumerate(funders):
            programs = f.get('known_programs', [])
            programs_text = ', '.join(programs) if programs else 'N/A'

            lines.append(f"""**{i+1}. {f.get('funder_name', 'Unknown')}** ({f.get('country', '?')})
- **Relevance:** {f.get('relevance', 'N/A').upper()}
- **Why:** {f.get('relevance_reasoning', 'N/A')}
- **Programs:** {programs_text}
- **Typical Amount:** {f.get('typical_amount', 'N/A')} | **Duration:** {f.get('typical_duration', 'N/A')}
- **Eligibility:** {f.get('eligibility_notes', 'N/A')}
- **Tip:** {f.get('application_tip', 'N/A')}
- **Homepage:** {f.get('homepage_url', 'N/A')}
""")
        return "\n".join(lines)

    def _format_figure_analyses(self, figures):
        """Format per-figure analyses for the report"""
        if not figures:
            return "No figures analyzed"

        lines = []
        for fig in figures:
            fig_num = fig.get('figure_number', '?')
            page = fig.get('page', '?')
            chart_type = fig.get('chart_type_detected', 'unknown')
            if isinstance(chart_type, list):
                chart_type = ', '.join(str(c) for c in chart_type)
            chart_type = str(chart_type)
            score = fig.get('overall_figure_score', 'N/A')
            priority = fig.get('priority', 'minor')
            if isinstance(priority, list):
                priority = priority[0] if priority else 'minor'
            priority = str(priority)
            appropriate = fig.get('chart_type_appropriate')
            appropriate_text = '✅ Yes' if appropriate else ('❌ No' if appropriate is False else 'N/A')

            color_assess = fig.get('color_assessment', {})
            color_score = color_assess.get('score', 'N/A') if isinstance(color_assess, dict) else 'N/A'
            axis_assess = fig.get('axis_assessment', {})
            axis_score = axis_assess.get('score', 'N/A') if isinstance(axis_assess, dict) else 'N/A'
            ink_assess = fig.get('data_ink_ratio', {})
            ink_score = ink_assess.get('score', 'N/A') if isinstance(ink_assess, dict) else 'N/A'
            legend_assess = fig.get('legend_assessment', {})
            legend_score = legend_assess.get('score', 'N/A') if isinstance(legend_assess, dict) else 'N/A'

            strengths = fig.get('strengths', [])
            if not isinstance(strengths, list):
                strengths = [str(strengths)] if strengths else []
            improvements = fig.get('improvements', [])
            if not isinstance(improvements, list):
                improvements = [str(improvements)] if improvements else []

            lines.append(f"""**Figure {fig_num}** (Page {page}) — {chart_type.title()} — Score: {score}/5 — Priority: {priority.upper()}
- **Chart Type Appropriate:** {appropriate_text}
- **Color:** {color_score}/5 | **Axes:** {axis_score}/5 | **Data-Ink:** {ink_score}/5 | **Legend:** {legend_score}/5
- **Strengths:** {', '.join(strengths) if strengths else 'None identified'}
- **Improvements:** {', '.join(improvements) if improvements else 'None needed'}
""")
        return "\n".join(lines)

    def _format_writing_metrics(self, metrics):
        """Format quantitative writing metrics for the report"""
        if not metrics:
            return "No metrics available"
        return f"""- **Avg Sentence Length:** {metrics.get('avg_sentence_length', 'N/A')} words
- **Max Sentence Length:** {metrics.get('max_sentence_length', 'N/A')} words
- **Passive Voice Ratio:** {metrics.get('passive_voice_ratio', 0):.0%}
- **Hedge Words:** {metrics.get('hedge_word_count', 0)}
- **Filler Words:** {metrics.get('filler_word_count', 0)}
- **Transition Words:** {metrics.get('transition_word_count', 0)}
- **Unique Word Ratio:** {metrics.get('unique_word_ratio', 0):.0%}
- **Sentences >40 Words:** {metrics.get('sentences_over_40_words', 0)}"""

    def _format_section_writing(self, sections):
        """Format per-section writing analysis for the report"""
        if not sections:
            return "No sections analyzed"

        lines = []
        for name, analysis in sections.items():
            score = analysis.get('overall_section_score', 'N/A')
            lines.append(f"""**{name.title()}** — Score: {score}/5
- Clarity: {analysis.get('clarity', 'N/A')}/5 | Conciseness: {analysis.get('conciseness', 'N/A')}/5 | Tone: {analysis.get('academic_tone', 'N/A')}/5
- Structure: {analysis.get('structure', 'N/A')}/5 | Precision: {analysis.get('precision', 'N/A')}/5 | Section-Specific: {analysis.get('section_specific', 'N/A')}/5
- Strengths: {', '.join(analysis.get('strengths', [])) if analysis.get('strengths') else 'None'}
- Weaknesses: {', '.join(analysis.get('weaknesses', [])) if analysis.get('weaknesses') else 'None'}
""")
        return "\n".join(lines)

    def generate_report(self, sections, methods, results, visualization, writing, citations, plagiarism, journals, funding, paper_type="original_research"):
        """Generate final markdown report"""

        report = f"""# RESEARCH PAPER ANALYSIS REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📄 PAPER OVERVIEW

**Title:** {sections.get('title', 'N/A')}
**Paper Type:** {paper_type.replace('_', ' ').title()}

**Abstract:**
{sections.get('abstract', 'Not found')[:800]}...

---

## 🔬 METHODOLOGY ASSESSMENT (Agent 1)

**Overall Quality Score:** {methods['overall_quality']}/5

### Sample Size
- **N:** {methods['sample_size']['n']}
- **Adequate:** {'✅ Yes' if methods['sample_size']['adequate'] else '❌ No'}
- **Power Calculation:** {methods['sample_size']['power_calculation']}
- **Comment:** {methods['sample_size']['comment']}

### Study Design
- **Type:** {methods['study_design']['type']}
- **Quality Score:** {methods['study_design']['quality_score']}/5
- **Appropriateness:** {methods['study_design']['appropriateness']}

### Statistical Methods
- **Methods Used:** {', '.join(methods['statistical_methods']['methods_used']) if methods['statistical_methods']['methods_used'] else 'None identified'}
- **Appropriate:** {'✅ Yes' if methods['statistical_methods']['appropriate'] else '❌ No'}
- **Issues:** {', '.join(methods['statistical_methods']['issues']) if methods['statistical_methods']['issues'] else 'None identified'}

### Identified Biases
{chr(10).join(f"- {b}" for b in methods['biases']['identified']) if methods['biases']['identified'] else 'None identified'}

**How Addressed:** {methods['biases']['comment']}

### Reproducibility
**Score:** {methods['reproducibility']['score']}/5
{methods['reproducibility']['comment']}

### Critical Issues
{chr(10).join(f"⚠️ {issue}" for issue in methods['critical_issues']) if methods['critical_issues'] else '✅ None identified'}

### Strengths
{chr(10).join(f"✅ {strength}" for strength in methods['strengths']) if methods['strengths'] else 'None identified'}

---

## 📊 KEY FINDINGS (Agent 2)

**Primary Outcome:** {results['primary_outcome']['measure']}

**Result:** {results['primary_outcome']['result']}
- **Statistically Significant:** {'✅ Yes' if results['primary_outcome']['statistically_significant'] else '❌ No'}
- **P-value:** {results['primary_outcome']['p_value']}

### Main Findings
{chr(10).join(f'''
**Finding {i+1}:** {f['finding']}
- Statistic: {f['statistic']}
- P-value: {f['p_value']}
- CI: {f.get('confidence_interval', 'N/A')}
''' for i, f in enumerate(results['key_findings'])) if results['key_findings'] else 'No findings extracted'}

### Effect Sizes
{chr(10).join(f"- **{e['metric']}:** {e['value']} ({e['interpretation']}) - {e['clinical_significance']}" for e in results['effect_sizes']) if results['effect_sizes'] else 'None reported'}

### Secondary Outcomes
{chr(10).join(f"- **{o['outcome']}:** {o['result']}" for o in results['secondary_outcomes']) if results['secondary_outcomes'] else 'None reported'}

**Main Conclusion:** {results['main_conclusion']}

**Strength of Evidence:** {results['strength_of_evidence'].upper()}

---

## 📈 DATA VISUALIZATION ASSESSMENT (Agent 7)

**Figures Analyzed:** {visualization['figures_analyzed']}
**Overall Quality:** {visualization['overall_quality']}/5

### Overall Assessment
{visualization.get('overall_assessment', 'N/A')}

### Per-Figure Analysis
{self._format_figure_analyses(visualization.get('figures', []))}

### Common Patterns
{chr(10).join(f"- {p}" for p in visualization.get('common_patterns', [])) if visualization.get('common_patterns') else 'None identified'}

### Best Practice Violations
{chr(10).join(f"⚠️ {v}" for v in visualization.get('best_practice_violations', [])) if visualization.get('best_practice_violations') else '✅ None identified'}

### Visualization Strengths
{chr(10).join(f"✅ {s}" for s in visualization.get('strengths', [])) if visualization.get('strengths') else 'None identified'}

### Recommendations
{chr(10).join(f"- {r}" for r in visualization.get('recommendations', [])) if visualization.get('recommendations') else 'None'}

---

## ✍️ WRITING QUALITY (Agent 8)

**Overall Writing Score:** {writing.get('overall_writing_score', 'N/A')}/5
**Readability Level:** {writing.get('readability_level', 'N/A')}

### Overall Assessment
{writing.get('overall_assessment', 'N/A')}

### Quantitative Metrics
{self._format_writing_metrics(writing.get('quantitative_metrics', {}))}

### Section-by-Section Analysis
{self._format_section_writing(writing.get('sections', {}))}

### Cross-Section Patterns
{chr(10).join(f"- {p}" for p in writing.get('cross_section_patterns', [])) if writing.get('cross_section_patterns') else 'None identified'}

### Top Improvements
{chr(10).join(f"**{imp.get('priority', '?')}.** {imp.get('issue', 'N/A')}: {imp.get('detail', '')}" for imp in writing.get('top_improvements', [])) if writing.get('top_improvements') else 'None identified'}

### Style Guide References
{chr(10).join(f"- {ref}" for ref in writing.get('style_guide_references', [])) if writing.get('style_guide_references') else 'None'}

---

## 🔗 RELATED RESEARCH (Agent 3)

**Literature Quality:** {citations['literature_quality'].upper()}

### Supporting Evidence
{chr(10).join(f"✅ **{p['title']}** ({p['year']}): {p['relevance']}" for p in citations['supporting_papers']) if citations['supporting_papers'] else 'No supporting papers identified'}

### Conflicting Evidence
{chr(10).join(f"❌ **{p['title']}** ({p['year']}): {p['conflict']}" for p in citations['conflicting_papers']) if citations['conflicting_papers'] else 'No conflicts identified'}

### Research Gaps
{chr(10).join(f"💡 {gap}" for gap in citations['research_gaps'])}

### Citation Context
{citations['citation_context']}

---

## 🚨 PLAGIARISM & INTEGRITY CHECK (Agent 4)

**Risk Score:** {plagiarism['plagiarism_risk_score']}/100
**Risk Level:** {plagiarism['risk_level'].upper()}

### Missing Citations ({len(plagiarism['missing_citations'])})
{chr(10).join(f'''
**{i+1}.** "{mc['text']}"
- **Reason:** {mc['reason']}
- **Severity:** {mc['severity'].upper()}
''' for i, mc in enumerate(plagiarism['missing_citations'])) if plagiarism['missing_citations'] else '✅ None identified'}

### Suspicious Sections ({len(plagiarism['suspicious_sections'])})
{chr(10).join(f'''
**{i+1}.** {s['issue']}
- **Text:** "{s['text'][:100]}..."
- **Recommendation:** {s['recommendation']}
''' for i, s in enumerate(plagiarism['suspicious_sections'])) if plagiarism['suspicious_sections'] else '✅ None identified'}

### Overall Assessment
{plagiarism['overall_assessment']}

### Recommendations
{chr(10).join(f"- {rec}" for rec in plagiarism['recommendations'])}

---

## 📚 JOURNAL RECOMMENDATIONS (Agent 5)

**Search Queries Used:** {', '.join(journals.get('search_queries_used', [])) if journals.get('search_queries_used') else 'N/A'}
**Journals Analyzed:** {journals.get('journals_found', 0)}
**Recommendation Confidence:** {journals.get('recommendation_confidence', 'unknown').upper()}

### Primary Recommendations (Best Fit)
{self._format_journal_recommendations(journals.get('primary_recommendations', []))}

### Secondary Recommendations (Backup Options)
{self._format_journal_recommendations(journals.get('secondary_recommendations', []))}

### Publication Strategy
{journals.get('publication_strategy', 'No strategy available')}

### Key Strengths for Submission
{chr(10).join(f"- {s}" for s in journals.get('key_strengths_for_submission', [])) if journals.get('key_strengths_for_submission') else 'None identified'}

### Potential Concerns for Reviewers
{chr(10).join(f"- {c}" for c in journals.get('potential_concerns_for_reviewers', [])) if journals.get('potential_concerns_for_reviewers') else 'None identified'}

---

## 💰 FUNDING RECOMMENDATIONS (Agent 6)

**Search Queries Used:** {', '.join(funding.get('search_queries_used', [])) if funding.get('search_queries_used') else 'N/A'}
**Funders Analyzed:** {funding.get('funders_found', 0)}
**Funded Papers Found:** {funding.get('total_similar_funded_papers', 0)}
**Data Confidence:** {funding.get('data_confidence', 'unknown').upper()}

### Funding Landscape
{funding.get('funding_landscape', 'No data available')}

### Primary Funding Sources (Best Fit)
{self._format_funding_recommendations(funding.get('primary_funders', []))}

### Secondary Funding Sources (Additional Options)
{self._format_funding_recommendations(funding.get('secondary_funders', []))}

### Funding Strategy
{funding.get('funding_strategy', 'No strategy available')}

---

## 🎯 FINAL SUMMARY

**Methodology Quality:** {methods['overall_quality']}/5
**Evidence Strength:** {results['strength_of_evidence'].upper()}
**DataViz Quality:** {visualization['overall_quality']}/5
**Writing Quality:** {writing.get('overall_writing_score', 'N/A')}/5
**Plagiarism Risk:** {plagiarism['risk_level'].upper()}
**Top Journal Match:** {journals['primary_recommendations'][0]['journal_name'] if journals.get('primary_recommendations') else 'N/A'}
**Top Funder Match:** {funding['primary_funders'][0]['funder_name'] if funding.get('primary_funders') else 'N/A'}
**Recommendation Confidence:** {journals.get('recommendation_confidence', 'unknown').upper()}

---

*Report generated by Research Paper Analyzer - 8 AI Agents*
"""
        
        return report


# CLI Interface
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python workflow.py <path_to_pdf>")
        print("\nExample: python workflow.py sample_paper.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"❌ Error: File not found: {pdf_path}")
        sys.exit(1)
    
    workflow = PaperAnalyzerWorkflow()
    report = workflow.run(pdf_path)