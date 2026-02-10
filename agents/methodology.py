from openai import AzureOpenAI
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION")
)

class MethodologyCritic:
    """Agent 1: Analyzes research methodology"""
    
    def __init__(self):
        self.model = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        
        self.system_prompt = """You are a research methodology expert.

You will receive the Methods section as the primary text, plus additional context from the Abstract and Results sections (if available). Use ALL provided sections to extract information — sample sizes, study design details, and statistical methods are often mentioned outside of Methods.

IMPORTANT: Numbers may be written as words (e.g. "ten" = 10, "twenty-three" = 23, "one hundred" = 100). Always convert written-out numbers to digits. Sample size information includes: number of participants/patients, number of sites/hospitals/centers, cohort sizes, groups — look for ALL of these.

Analyze the methodology and evaluate:

1. **Sample Size**
   - Extract ALL numeric information: total participants (n), number of sites/centers, group sizes
   - Numbers written as words count (e.g. "ten hospitals" → n_sites=10)
   - Is it adequate for the research question?
   - Was power calculation mentioned?
   - Comment on statistical power

2. **Study Design**
   - Type: RCT, observational, cohort, case-control, etc.
   - Quality rating (1-5)
   - Appropriateness for research question

3. **Statistical Methods**
   - Are methods appropriate for data type?
   - Common mistakes identified?

4. **Potential Biases**
   - Selection bias, measurement bias, confounding
   - How well were they addressed?

5. **Reproducibility**
   - Can another researcher replicate this?
   - Are methods described clearly enough?

Return JSON:
{
  "sample_size": {
    "n": number,
    "adequate": boolean,
    "power_calculation": "mentioned/not_mentioned",
    "comment": "brief assessment"
  },
  "study_design": {
    "type": "RCT/observational/cohort/etc",
    "quality_score": 1-5,
    "appropriateness": "brief comment"
  },
  "statistical_methods": {
    "methods_used": ["method1", "method2"],
    "appropriate": boolean,
    "issues": ["issue1", "issue2"] or []
  },
  "biases": {
    "identified": ["bias1", "bias2"],
    "addressed": boolean,
    "comment": "how well handled"
  },
  "reproducibility": {
    "score": 1-5,
    "comment": "can this be replicated?"
  },
  "overall_quality": 1-5,
  "critical_issues": ["issue1", "issue2"] or [],
  "strengths": ["strength1", "strength2"]
}
"""
    
    def analyze(self, methods_text, abstract="", results_text=""):
        """Analyze methods section with additional context from abstract and results"""

        print("🔬 Agent 1 (Methodology Critic) analyzing...\n")

        user_content = f"## Methods Section\n\n{methods_text}"
        if abstract:
            user_content += f"\n\n## Abstract (additional context)\n\n{abstract}"
        if results_text:
            user_content += f"\n\n## Results Section (additional context)\n\n{results_text}"

        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            temperature=0.3  # Lower = more consistent
        )
        
        result = json.loads(response.choices[0].message.content)
        
        print(f"✅ Quality Score: {result['overall_quality']}/5")
        print(f"✅ Sample Size: n={result['sample_size']['n']} ({'adequate' if result['sample_size']['adequate'] else 'inadequate'})")
        print(f"✅ Reproducibility: {result['reproducibility']['score']}/5\n")
        
        return result


# Test
if __name__ == "__main__":
    critic = MethodologyCritic()
    
    # Test with sample methods section
    test_methods = """
    Methods: We conducted a randomized controlled trial with 150 participants 
    (75 per group) recruited from three university hospitals. Sample size was 
    determined via power calculation (80% power, α=0.05, expected effect size d=0.5).
    
    Participants were randomly assigned using computer-generated randomization to either
    intervention or control group. Primary outcome was measured using validated 
    questionnaire (Cronbach's α=0.89). 
    
    Statistical analysis used independent t-tests for continuous variables and 
    chi-square for categorical data. Intention-to-treat analysis was performed.
    All analyses used SPSS v28, significance level p<0.05.
    """
    
    result = critic.analyze(test_methods)
    
    print("\n" + "="*50)
    print("FULL ANALYSIS:")
    print("="*50)
    print(json.dumps(result, indent=2))