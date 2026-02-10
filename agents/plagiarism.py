from openai import AzureOpenAI
from dotenv import load_dotenv
import os
import json
import re

load_dotenv()


class PlagiarismDetector:
    """Agent 4: Detects potential plagiarism and missing citations"""

    def __init__(self):
        self.client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION")
        )
        self.model = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

        self.system_prompt_original = """You are a plagiarism detection expert.

Analyze this ORIGINAL RESEARCH paper for potential academic integrity issues:

1. **Self-Plagiarism Indicators**
   - Repetitive phrasing patterns
   - Overly similar sentence structures
   - Recycled content signs

2. **Missing Citations**
   - Specific claims without references
   - Common knowledge vs cited claims
   - Statistical facts needing sources

3. **Paraphrasing Issues**
   - Text that seems paraphrased but uncredited
   - Suspiciously technical language without attribution

4. **Text Quality Issues**
   - Inconsistent writing style (suggests copy-paste)
   - Sudden vocabulary/complexity shifts

Return JSON:
{
  "plagiarism_risk_score": 0-100,
  "risk_level": "low/medium/high",
  "missing_citations": [
    {
      "text": "excerpt needing citation",
      "reason": "why it needs citation",
      "severity": "low/medium/high"
    }
  ],
  "suspicious_sections": [
    {
      "text": "suspicious excerpt",
      "issue": "what's suspicious",
      "recommendation": "what to do"
    }
  ],
  "writing_quality_flags": [
    {
      "issue": "description",
      "location": "section/paragraph"
    }
  ],
  "overall_assessment": "brief summary",
  "recommendations": ["rec1", "rec2"]
}
"""

        self.system_prompt_review = """You are a plagiarism detection expert.

You are analyzing a REVIEW / META-ANALYSIS paper. Review papers naturally summarize, synthesize, and paraphrase existing research — this is EXPECTED and NOT plagiarism.

Adjust your analysis accordingly:
- Paraphrasing existing findings is NORMAL for reviews — do NOT flag this as suspicious
- Focus on: verbatim copying without quotation marks, missing citation numbers where claims are made, and inconsistent writing style that suggests copy-paste from multiple sources
- Reference numbers like [1], [2,3], (4), (5,6) ARE citations — do not flag these as missing
- A review paper should score LOW (0-30) unless there is actual evidence of verbatim copying or systematic missing attributions

Analyze for:
1. **Verbatim Copying** - Exact sentences copied without quotation marks
2. **Missing Citations** - Specific factual claims with NO reference number at all
3. **Style Inconsistencies** - Sudden shifts suggesting copy-paste from different sources
4. **Self-Plagiarism** - Recycled text from authors' own previous work

Return JSON:
{
  "plagiarism_risk_score": 0-100,
  "risk_level": "low/medium/high",
  "missing_citations": [
    {
      "text": "excerpt needing citation",
      "reason": "why it needs citation",
      "severity": "low/medium/high"
    }
  ],
  "suspicious_sections": [
    {
      "text": "suspicious excerpt",
      "issue": "what's suspicious",
      "recommendation": "what to do"
    }
  ],
  "writing_quality_flags": [
    {
      "issue": "description",
      "location": "section/paragraph"
    }
  ],
  "overall_assessment": "brief summary",
  "recommendations": ["rec1", "rec2"]
}
"""

    def split_sentences(self, text):
        """Split text into sentences"""
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 20]

    def analyze(self, paper_text, paper_type="original_research"):
        """Analyze for plagiarism indicators"""

        print("🚨 Agent 4 (Plagiarism Detector) analyzing...\n")

        # Split into sentences for analysis
        sentences = self.split_sentences(paper_text)
        print(f"✅ Analyzing {len(sentences)} sentences\n")

        # Select prompt based on paper type
        if paper_type in ("review", "meta_analysis"):
            system_prompt = self.system_prompt_review
            print("ℹ️  Using review-adjusted analysis criteria\n")
        else:
            system_prompt = self.system_prompt_original

        # Send up to 50k chars (GPT-4o has 128k context)
        analysis_text = paper_text[:50000]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this text:\n\n{analysis_text}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )

        result = json.loads(response.choices[0].message.content)

        print(f"✅ Risk Score: {result['plagiarism_risk_score']}/100")
        print(f"✅ Risk Level: {result['risk_level']}")
        print(f"✅ Missing Citations: {len(result['missing_citations'])}")
        print(f"✅ Suspicious Sections: {len(result['suspicious_sections'])}\n")

        return result


# Test
if __name__ == "__main__":
    detector = PlagiarismDetector()
    
    test_text = """
    Introduction: Depression affects millions worldwide. Recent studies have shown
    that mindfulness meditation reduces symptoms by 40-60%. The exact mechanisms 
    remain unclear, though neuroimaging studies suggest changes in prefrontal cortex 
    activity.
    
    Methods: We recruited 150 participants from three hospitals. All participants
    completed the Beck Depression Inventory at baseline and follow-up. The intervention
    consisted of eight weekly 90-minute sessions based on Mindfulness-Based Stress
    Reduction protocol.
    
    Results: Participants in the intervention group showed significant improvements
    (mean change = 12.5 points, p<0.001). These results are consistent with meta-analyses
    showing medium to large effect sizes for mindfulness interventions.
    """
    
    result = detector.analyze(test_text)
    
    print("\n" + "="*50)
    print("PLAGIARISM ANALYSIS:")
    print("="*50)
    print(json.dumps(result, indent=2))