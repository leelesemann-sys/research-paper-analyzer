from openai import AzureOpenAI
from dotenv import load_dotenv
import os
import json
import re
from collections import Counter

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION")
)


class WritingQualityCoach:
    """Agent 8: Evaluates academic writing quality against style guide standards"""

    PASSIVE_PATTERNS = [
        r'\b(is|are|was|were|been|being|be)\s+\w+ed\b',
        r'\b(is|are|was|were|been|being|be)\s+\w+en\b',
    ]

    HEDGE_WORDS = [
        'might', 'perhaps', 'possibly', 'somewhat', 'arguably',
        'relatively', 'fairly', 'rather', 'quite', 'seems',
        'appears', 'suggests', 'may', 'could', 'tend', 'likely',
        'probable', 'potential', 'presumably'
    ]

    FILLER_WORDS = [
        'very', 'really', 'basically', 'actually', 'literally',
        'just', 'simply', 'clearly', 'obviously', 'of course',
        'it is worth noting', 'it should be noted', 'needless to say',
        'it is important to note', 'it goes without saying',
        'as a matter of fact', 'in point of fact'
    ]

    TRANSITION_WORDS = [
        'however', 'therefore', 'moreover', 'furthermore',
        'nevertheless', 'consequently', 'additionally',
        'in contrast', 'similarly', 'specifically',
        'for example', 'in particular', 'notably',
        'conversely', 'meanwhile', 'subsequently',
        'accordingly', 'hence', 'thus', 'nonetheless'
    ]

    SECTION_STANDARDS = {
        "abstract": """ABSTRACT standards:
- Must be self-contained: a reader should understand the study without reading the paper
- Structured format preferred (Background, Methods, Results, Conclusion)
- Concise: typically 150-300 words
- No citations, no abbreviations without definition
- Should state the main finding with key quantitative results
- Avoid vague statements like "results are discussed"
""",
        "introduction": """INTRODUCTION standards:
- Funnel structure: broad context → specific gap → your contribution
- Should establish WHY this research matters (significance)
- Must clearly state the research gap or unanswered question
- Ends with hypothesis, research question, or objectives
- Each paragraph should build on the previous one (logical flow)
- Citations should be current and relevant (not excessive)
- Avoid reviewing ALL literature — focus on what's directly relevant
""",
        "methods": """METHODS standards:
- Precise enough for replication by another researcher
- Passive voice is acceptable and common in this section
- Logical or chronological order (study design → participants → procedure → analysis)
- Must specify: sample/participants, instruments/materials, procedure, statistical analysis
- Use past tense (what was done)
- Avoid justifying standard methods — only justify unusual choices
- Include ethical approvals if applicable
""",
        "results": """RESULTS standards:
- Objective reporting only — NO interpretation (save for Discussion)
- Present findings in order of importance or following the research questions
- Include effect sizes, confidence intervals, p-values where appropriate
- Text should complement tables/figures, not repeat them verbatim
- Use past tense
- Clearly distinguish significant from non-significant results
- Avoid subjective qualifiers ("dramatically increased" → "increased by 45%")
""",
        "discussion": """DISCUSSION standards:
- Begin with a brief restatement of the main finding
- Interpret results in context of existing literature (compare and contrast)
- Address ALL results, including unexpected or negative findings
- Acknowledge limitations honestly and specifically
- Do NOT introduce new data or results
- Discuss practical implications and theoretical contributions
- Suggest future research directions
- Maintain nuanced tone — avoid overclaiming
""",
        "conclusion": """CONCLUSION standards:
- Brief and focused (typically 1-2 paragraphs)
- Restate the main contribution without repeating the abstract
- No new arguments, data, or citations
- State practical implications
- May include future research directions (briefly)
- Should leave the reader with a clear take-away message
"""
    }

    def __init__(self):
        self.model = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

        self.section_prompt = """You are an expert academic writing coach who evaluates scientific paper sections
against established style guide standards (APA 7th Edition, Strunk & White, Schimel "Writing Science",
Sword "Stylish Academic Writing", Day & Gastel "How to Write and Publish a Scientific Paper").

You will receive:
1. The section text
2. Pre-computed quantitative metrics (sentence lengths, passive voice ratio, etc.)
3. Section-specific writing standards

Evaluate the section on these 6 dimensions (each 1-5):
- **clarity**: Is the writing clear and understandable for the target audience?
- **conciseness**: Is every sentence necessary? Any filler or redundancy?
- **academic_tone**: Formal but not stilted? Appropriate hedging without excess?
- **structure**: Logical paragraph organization? Good transitions? Coherent flow?
- **precision**: Exact terminology? No vague language? Specific claims with evidence?
- **section_specific**: Does it meet the specific standards for THIS section type?

Also provide:
- overall_section_score: weighted average (1-5)
- strengths: 2-4 specific things done well
- weaknesses: 2-4 specific issues
- suggestions: 2-4 actionable improvement suggestions
- problematic_sentences: up to 5 specific sentences with issues and concrete rewrite suggestions

For problematic_sentences, quote the EXACT text from the paper, explain the issue,
and provide a specific rewrite suggestion.

When referencing writing standards, cite the specific guide:
e.g., "APA 7th, Section 4.13: Prefer active voice" or "Schimel: One point per paragraph"

Return valid JSON:
{
    "clarity": 1-5,
    "conciseness": 1-5,
    "academic_tone": 1-5,
    "structure": 1-5,
    "precision": 1-5,
    "section_specific": 1-5,
    "overall_section_score": float,
    "strengths": ["..."],
    "weaknesses": ["..."],
    "suggestions": ["..."],
    "problematic_sentences": [
        {"text": "exact quote", "issue": "what's wrong", "suggestion": "rewritten version"}
    ]
}"""

        self.synthesis_prompt = """You are an expert academic writing coach providing a holistic assessment
of a research paper's writing quality.

Given per-section analyses and overall quantitative metrics, provide:

1. overall_writing_score (1-5): Weighted average across sections
2. overall_assessment: 3-5 sentences summarizing the paper's writing quality
3. cross_section_patterns: Recurring issues or strengths across multiple sections
4. top_improvements: The 3 most impactful changes the author should make (prioritized)
5. style_guide_references: 3-5 specific style guide citations relevant to the findings
6. readability_level: "basic academic" / "advanced academic" / "expert only" / "mixed"
7. data_confidence: "high" / "medium" / "low"

For top_improvements, be SPECIFIC and ACTIONABLE:
- Bad: "Improve writing style"
- Good: "Reduce passive voice from 42% to under 25% — rewrite key result sentences in active voice (e.g., 'We found X' instead of 'X was found')"

Return valid JSON:
{
    "overall_writing_score": float,
    "overall_assessment": "...",
    "cross_section_patterns": ["..."],
    "top_improvements": [
        {"priority": 1, "issue": "...", "detail": "..."}
    ],
    "style_guide_references": ["..."],
    "readability_level": "...",
    "data_confidence": "high/medium/low"
}"""

    # --- Quantitative Metrics (pure Python) ---

    def _compute_metrics(self, text):
        """Compute quantitative text metrics without LLM"""
        if not text or len(text.strip()) < 50:
            return self._empty_metrics()

        try:
            # Split into sentences (handle abbreviations like "et al.", "Fig.", "e.g.")
            cleaned = re.sub(r'\b(et al|Fig|fig|Eq|eq|vs|Dr|Mr|Mrs|Ms|Prof|Inc|Ltd|Jr|Sr)\.',
                             r'\1DOTPLACEHOLDER', text)
            cleaned = re.sub(r'(\d)\.(\d)', r'\1DOTPLACEHOLDER\2', cleaned)
            sentences = [s.strip() for s in re.split(r'[.!?]+', cleaned) if len(s.strip()) > 5]

            if not sentences:
                return self._empty_metrics()

            # Sentence lengths
            sentence_lengths = [len(s.split()) for s in sentences]
            avg_sentence_length = sum(sentence_lengths) / len(sentence_lengths)
            max_sentence_length = max(sentence_lengths)
            sentences_over_40 = sum(1 for l in sentence_lengths if l > 40)

            # Paragraphs
            paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 20]
            avg_paragraph_length = (sum(len(p.split()) for p in paragraphs) / len(paragraphs)) if paragraphs else 0

            # Words
            words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
            total_words = len(words) if words else 1
            unique_words = set(words)
            unique_word_ratio = len(unique_words) / total_words

            # Word repetitions (top non-stopword repeats)
            stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                         'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
                         'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                         'could', 'should', 'may', 'might', 'can', 'shall', 'that', 'this',
                         'these', 'those', 'it', 'its', 'as', 'not', 'no', 'if', 'than',
                         'which', 'who', 'whom', 'what', 'when', 'where', 'how', 'all',
                         'each', 'both', 'more', 'most', 'other', 'some', 'such', 'only',
                         'also', 'into', 'over', 'after', 'before', 'between', 'through',
                         'during', 'about', 'their', 'our', 'we', 'they', 'them', 'there'}
            content_words = [w for w in words if w not in stopwords and len(w) > 3]
            word_counts = Counter(content_words)
            top_repeats = word_counts.most_common(10)

            # Passive voice
            text_lower = text.lower()
            passive_count = 0
            for pattern in self.PASSIVE_PATTERNS:
                passive_count += len(re.findall(pattern, text_lower))
            passive_ratio = passive_count / len(sentences) if sentences else 0

            # Hedge words
            hedge_count = sum(len(re.findall(r'\b' + re.escape(h) + r'\b', text_lower))
                              for h in self.HEDGE_WORDS)

            # Filler words/phrases
            filler_count = sum(len(re.findall(re.escape(f), text_lower))
                               for f in self.FILLER_WORDS)

            # Transition words
            transition_count = sum(len(re.findall(r'\b' + re.escape(t) + r'\b', text_lower))
                                   for t in self.TRANSITION_WORDS)

            return {
                "avg_sentence_length": round(avg_sentence_length, 1),
                "max_sentence_length": max_sentence_length,
                "avg_paragraph_length": round(avg_paragraph_length, 1),
                "total_sentences": len(sentences),
                "total_words": total_words,
                "passive_voice_ratio": round(passive_ratio, 2),
                "hedge_word_count": hedge_count,
                "filler_word_count": filler_count,
                "transition_word_count": transition_count,
                "unique_word_ratio": round(unique_word_ratio, 2),
                "sentences_over_40_words": sentences_over_40,
                "top_repeated_words": top_repeats[:5]
            }

        except Exception as e:
            print(f"   Warning: Metrics computation error: {e}")
            return self._empty_metrics()

    def _empty_metrics(self):
        """Return empty metrics structure"""
        return {
            "avg_sentence_length": 0,
            "max_sentence_length": 0,
            "avg_paragraph_length": 0,
            "total_sentences": 0,
            "total_words": 0,
            "passive_voice_ratio": 0,
            "hedge_word_count": 0,
            "filler_word_count": 0,
            "transition_word_count": 0,
            "unique_word_ratio": 0,
            "sentences_over_40_words": 0,
            "top_repeated_words": []
        }

    # --- LLM Analysis ---

    def _analyze_section(self, section_name, section_text, metrics):
        """Analyze a single section's writing quality"""
        if not section_text or len(section_text.strip()) < 50:
            return None

        standards = self.SECTION_STANDARDS.get(section_name, "General academic writing standards apply.")

        # Truncate very long sections
        text_to_analyze = section_text[:8000]

        prompt = f"""Analyze this {section_name.upper()} section's writing quality.

QUANTITATIVE METRICS (pre-computed from the text):
- Average sentence length: {metrics['avg_sentence_length']} words
- Longest sentence: {metrics['max_sentence_length']} words
- Total sentences: {metrics['total_sentences']}
- Passive voice ratio: {metrics['passive_voice_ratio']:.0%}
- Hedge words found: {metrics['hedge_word_count']}
- Filler words/phrases found: {metrics['filler_word_count']}
- Transition words: {metrics['transition_word_count']}
- Unique word ratio (type-token): {metrics['unique_word_ratio']:.0%}
- Sentences over 40 words: {metrics['sentences_over_40_words']}
- Most repeated content words: {', '.join(f'{w}({c})' for w, c in metrics.get('top_repeated_words', []))}

SECTION-SPECIFIC STANDARDS:
{standards}

TEXT TO ANALYZE:
{text_to_analyze}"""

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.section_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=2000
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"   Warning: Section analysis failed for {section_name}: {e}")
            return {
                "clarity": 0, "conciseness": 0, "academic_tone": 0,
                "structure": 0, "precision": 0, "section_specific": 0,
                "overall_section_score": 0,
                "strengths": [], "weaknesses": [f"Analysis failed: {e}"],
                "suggestions": [], "problematic_sentences": []
            }

    def _synthesize(self, section_analyses, overall_metrics):
        """Synthesize per-section results into overall assessment"""
        sections_summary = {}
        for name, analysis in section_analyses.items():
            if analysis:
                sections_summary[name] = {
                    "score": analysis.get("overall_section_score", 0),
                    "strengths": analysis.get("strengths", []),
                    "weaknesses": analysis.get("weaknesses", [])
                }

        prompt = f"""Synthesize this writing quality assessment.

PER-SECTION RESULTS:
{json.dumps(sections_summary, indent=2)}

OVERALL QUANTITATIVE METRICS:
{json.dumps(overall_metrics, indent=2)}

BENCHMARKS for reference:
- Average sentence length: 15-25 words is ideal for academic writing
- Passive voice: <25% is good, 25-35% acceptable, >35% excessive
- Hedge words: Some hedging is appropriate in academic writing, but excessive hedging weakens claims
- Unique word ratio: >0.40 indicates varied vocabulary
- Sentences >40 words: should be rare (<5% of total)

Provide your holistic assessment."""

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.synthesis_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=1500
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"   Warning: Synthesis failed: {e}")
            return {
                "overall_writing_score": 0,
                "overall_assessment": f"Synthesis failed: {e}",
                "cross_section_patterns": [],
                "top_improvements": [],
                "style_guide_references": [],
                "readability_level": "unknown",
                "data_confidence": "low"
            }

    def _empty_analysis(self, note="No text available for analysis"):
        """Return empty result structure"""
        return {
            "overall_writing_score": "N/A",
            "overall_assessment": note,
            "sections": {},
            "quantitative_metrics": self._empty_metrics(),
            "cross_section_patterns": [],
            "top_improvements": [],
            "style_guide_references": [],
            "readability_level": "unknown",
            "data_confidence": "low"
        }

    # --- Main Method ---

    def analyze(self, sections, paper_type="original_research"):
        """Analyze writing quality across all paper sections"""

        print("Writing Quality Coach) evaluating writing style...\n")

        # Check if we have any text to analyze
        analyzable_sections = {
            name: text for name, text in sections.items()
            if name in self.SECTION_STANDARDS and text and len(text.strip()) > 50
        }

        if not analyzable_sections:
            print("   No analyzable sections found\n")
            return self._empty_analysis("No paper sections with sufficient text found.")

        print(f"   Sections to analyze: {', '.join(analyzable_sections.keys())}")

        # Step 1: Compute metrics for full text and per section
        full_text = ' '.join(analyzable_sections.values())
        overall_metrics = self._compute_metrics(full_text)

        print(f"   Overall metrics computed:")
        print(f"     Avg sentence length: {overall_metrics['avg_sentence_length']} words")
        print(f"     Passive voice ratio: {overall_metrics['passive_voice_ratio']:.0%}")
        print(f"     Hedge words: {overall_metrics['hedge_word_count']}")
        print(f"     Filler words: {overall_metrics['filler_word_count']}")
        print(f"     Unique word ratio: {overall_metrics['unique_word_ratio']:.0%}\n")

        # Step 2: Analyze each section
        section_analyses = {}
        for name, text in analyzable_sections.items():
            print(f"   Analyzing {name}...")
            section_metrics = self._compute_metrics(text)
            analysis = self._analyze_section(name, text, section_metrics)
            if analysis:
                section_analyses[name] = analysis
                score = analysis.get('overall_section_score', '?')
                print(f"     Score: {score}/5")

        if not section_analyses:
            print("   No sections could be analyzed\n")
            return self._empty_analysis("All section analyses failed.")

        # Step 3: Synthesize
        print(f"\n   Synthesizing overall assessment...")
        synthesis = self._synthesize(section_analyses, overall_metrics)

        # Build final result
        result = {
            "overall_writing_score": synthesis.get("overall_writing_score", 0),
            "overall_assessment": synthesis.get("overall_assessment", ""),
            "sections": section_analyses,
            "quantitative_metrics": overall_metrics,
            "cross_section_patterns": synthesis.get("cross_section_patterns", []),
            "top_improvements": synthesis.get("top_improvements", []),
            "style_guide_references": synthesis.get("style_guide_references", []),
            "readability_level": synthesis.get("readability_level", "unknown"),
            "data_confidence": synthesis.get("data_confidence", "medium")
        }

        # Print summary
        score = result['overall_writing_score']
        sections_done = len(section_analyses)
        patterns = len(result['cross_section_patterns'])
        improvements = len(result['top_improvements'])

        print(f"\n   Overall Writing Score: {score}/5")
        print(f"   Sections Analyzed: {sections_done}")
        print(f"   Cross-Section Patterns: {patterns}")
        print(f"   Top Improvements: {improvements}")
        print(f"   Readability Level: {result['readability_level']}")
        print(f"   Data Confidence: {result['data_confidence'].upper()}\n")

        return result


# Test
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    # Quick standalone test with sample text
    coach = WritingQualityCoach()

    test_sections = {
        "abstract": """This study investigates the application of machine learning algorithms
for predicting stock market movements. It should be noted that previous research has shown
mixed results in this area. We basically utilized LSTM networks and gradient boosting methods
to analyze alternative data sources including sentiment analysis and satellite imagery.
Our results suggest that the proposed approach might potentially achieve somewhat better
performance compared to traditional methods. The findings clearly demonstrate that
machine learning could be a very useful tool for financial prediction.""",

        "introduction": """Stock market prediction has been a very important topic in finance
for a really long time. Many researchers have tried to predict stock prices using various
methods. However, it is worth noting that traditional approaches have shown limited success.
The efficient market hypothesis suggests that stock prices reflect all available information.
Nevertheless, recent advances in machine learning have opened new possibilities.
In this paper, we propose a novel approach that combines LSTM networks with alternative data.""",

        "methods": """Data was collected from Yahoo Finance API for the period 2015-2023.
The dataset consisted of daily stock prices for S&P 500 companies. Feature engineering
was performed to extract technical indicators. LSTM networks were implemented using
TensorFlow 2.x with the following architecture: 2 LSTM layers (128 and 64 units),
dropout of 0.2, and dense output layer. The model was trained using Adam optimizer
with learning rate 0.001. Cross-validation with 5 folds was used for evaluation.
Performance metrics included RMSE, MAE, and directional accuracy.""",

        "results": """The LSTM model achieved an RMSE of 0.023 on the test set, which was
significantly lower than the baseline model (RMSE=0.045, p<0.001). The gradient boosting
approach showed comparable performance with RMSE of 0.025. Directional accuracy was 62.3%
for the LSTM model and 60.1% for gradient boosting. When alternative data was incorporated,
LSTM performance dramatically improved to RMSE of 0.018.""",

        "discussion": """Our results demonstrate that machine learning approaches, particularly
LSTM networks, can effectively predict stock market movements. This finding is consistent
with previous studies by Zhang et al. (2020) and Kim et al. (2019). The improvement observed
when incorporating alternative data suggests that non-traditional features carry significant
predictive information. A limitation of our study is the relatively short time period analyzed.
Future research should explore longer time horizons and additional alternative data sources.""",

        "conclusion": """In conclusion, this study has shown that machine learning methods
can be effectively applied to stock market prediction. The key contribution is the
demonstration that alternative data sources improve prediction accuracy. These findings
have important implications for both researchers and practitioners in computational finance."""
    }

    result = coach.analyze(test_sections, "original_research")

    print("\n" + "=" * 50)
    print("WRITING QUALITY ANALYSIS:")
    print("=" * 50)
    print(json.dumps(result, indent=2, ensure_ascii=False))
