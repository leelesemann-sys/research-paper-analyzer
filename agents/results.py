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

class ResultsSynthesizer:
    """Agent 2: Extracts and synthesizes key findings"""
    
    def __init__(self):
        self.model = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        
        self.system_prompt = """You are a results analyst expert.

Extract and synthesize from the Results section:

1. **Primary Outcome**
   - What was the main outcome measured?
   - Clear definition

2. **Key Findings**
   - Main results with statistics
   - Include: point estimates, confidence intervals, p-values
   - Direction of effect

3. **Effect Sizes**
   - Calculate or extract effect sizes
   - Interpretation (small/medium/large)
   - Clinical vs statistical significance

4. **Secondary Outcomes**
   - Other important findings
   - Subgroup analyses

5. **Main Conclusion**
   - What's the take-home message?
   - Strength of evidence

Return JSON:
{
  "primary_outcome": {
    "measure": "what was measured",
    "result": "main finding with statistics",
    "statistically_significant": boolean,
    "p_value": "value or 'not reported'"
  },
  "key_findings": [
    {
      "finding": "description",
      "statistic": "test statistic and value",
      "p_value": "value",
      "confidence_interval": "CI if reported"
    }
  ],
  "effect_sizes": [
    {
      "metric": "Cohen's d / OR / RR / etc",
      "value": number,
      "interpretation": "small/medium/large",
      "clinical_significance": "clinically meaningful?"
    }
  ],
  "secondary_outcomes": [
    {
      "outcome": "description",
      "result": "finding"
    }
  ],
  "main_conclusion": "one sentence summary",
  "strength_of_evidence": "weak/moderate/strong",
  "limitations_noted": ["limitation1", "limitation2"]
}
"""
    
    def analyze(self, results_text):
        """Analyze results section"""
        
        print("📊 Agent 2 (Results Synthesizer) analyzing...\n")
        
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Extract key findings:\n\n{results_text}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
        
        print(f"✅ Primary Outcome: {result['primary_outcome']['measure']}")
        print(f"✅ Significant: {result['primary_outcome']['statistically_significant']}")
        print(f"✅ Key Findings: {len(result['key_findings'])} extracted")
        print(f"✅ Evidence: {result['strength_of_evidence']}\n")
        
        return result


# Test
if __name__ == "__main__":
    synthesizer = ResultsSynthesizer()
    
    test_results = """
    Results: The intervention group showed significantly greater improvement 
    compared to control (mean difference = 12.5 points, 95% CI: 8.2-16.8, 
    t(148)=5.84, p<0.001, Cohen's d=0.95). 
    
    At 3-month follow-up, 68% of intervention participants (51/75) achieved 
    clinical improvement compared to 32% (24/75) in control group (χ²=19.44, 
    p<0.001, OR=4.5, 95% CI: 2.3-8.9).
    
    Secondary outcomes showed intervention group had better quality of life 
    scores (mean difference = 8.3, p=0.003) and fewer adverse events (12% vs 28%, 
    p=0.012).
    
    Subgroup analysis revealed effects were consistent across age groups and 
    baseline severity. No serious adverse events were reported in either group.
    """
    
    result = synthesizer.analyze(test_results)
    
    print("\n" + "="*50)
    print("FULL SYNTHESIS:")
    print("="*50)
    print(json.dumps(result, indent=2))