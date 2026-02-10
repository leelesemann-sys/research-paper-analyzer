from openai import AzureOpenAI
from dotenv import load_dotenv
import os
import json
import requests
import time

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION")
)

class CitationHunter:
    """Agent 3: Finds related papers and analyzes citation context"""
    
    def __init__(self):
        self.model = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        self.semantic_scholar_api = "https://api.semanticscholar.org/graph/v1"
        
        self.system_prompt = """You are a citation and literature analysis expert.

Given a paper's title, abstract, and related papers from literature, analyze:

1. **Supporting Evidence**
   - Papers that support/confirm the findings
   - How do they align?

2. **Conflicting Evidence**
   - Papers with contradictory findings
   - What are the conflicts?
   - Possible explanations?

3. **Research Gaps**
   - What's missing from current literature?
   - Unanswered questions
   - Future research directions

4. **Most Relevant Papers**
   - Top 5 most relevant to this work
   - Why are they relevant?

Return JSON:
{
  "supporting_papers": [
    {
      "title": "paper title",
      "year": year,
      "relevance": "why it supports",
      "key_finding": "what it found"
    }
  ],
  "conflicting_papers": [
    {
      "title": "paper title",
      "year": year,
      "conflict": "nature of disagreement",
      "possible_explanation": "why might they differ?"
    }
  ],
  "research_gaps": [
    "gap 1: description",
    "gap 2: description"
  ],
  "top_relevant": [
    {
      "title": "paper title",
      "year": year,
      "relevance_score": 1-10,
      "why_relevant": "explanation"
    }
  ],
  "literature_quality": "weak/moderate/strong",
  "citation_context": "brief assessment of how well this fits existing literature"
}
"""
    
    def search_papers(self, query, limit=10):
        """Search Semantic Scholar for related papers with retry on rate limit"""

        url = f"{self.semantic_scholar_api}/paper/search"
        params = {
            "query": query,
            "limit": limit,
            "fields": "title,abstract,year,citationCount,authors"
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params, timeout=10)

                if response.status_code == 429:
                    wait_time = 2 ** (attempt + 1)  # 2s, 4s, 8s
                    print(f"⚠️  Rate limited by Semantic Scholar, retrying in {wait_time}s... ({attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                data = response.json()
                return data.get("data", [])
            except requests.exceptions.HTTPError as e:
                if "429" not in str(e):
                    print(f"⚠️  Semantic Scholar API error: {e}")
                    return []
            except Exception as e:
                print(f"⚠️  Semantic Scholar API error: {e}")
                return []

        print("⚠️  Semantic Scholar API: rate limit exceeded after retries")
        return []
    
    def analyze(self, paper_title, paper_abstract, search_query=None):
        """Analyze citations and related work"""
        
        print("🔗 Agent 3 (Citation Hunter) searching literature...\n")
        
        # Search for related papers
        if search_query is None:
            search_query = paper_title
        
        related_papers = self.search_papers(search_query)
        
        if not related_papers:
            print("⚠️  No related papers found\n")
            return {
                "supporting_papers": [],
                "conflicting_papers": [],
                "research_gaps": ["Unable to assess - no related papers found"],
                "top_relevant": [],
                "literature_quality": "unknown",
                "citation_context": "Could not retrieve related literature"
            }
        
        print(f"✅ Found {len(related_papers)} related papers\n")
        
        # Format related papers for LLM
        related_text = "\n\n".join([
            f"Title: {p['title']}\n"
            f"Year: {p.get('year', 'N/A')}\n"
            f"Citations: {p.get('citationCount', 0)}\n"
            f"Abstract: {(p.get('abstract') or 'Not available')[:300]}..."
            for p in related_papers[:8]  # Top 8
        ])
        
        # LLM analyzes relationships
        prompt = f"""
YOUR PAPER:
Title: {paper_title}
Abstract: {paper_abstract}

RELATED PAPERS FROM LITERATURE:
{related_text}

Analyze the relationship between your paper and the related literature.
"""
        
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.4
        )
        
        result = json.loads(response.choices[0].message.content)
        
        print(f"✅ Supporting papers: {len(result['supporting_papers'])}")
        print(f"✅ Conflicting papers: {len(result['conflicting_papers'])}")
        print(f"✅ Research gaps: {len(result['research_gaps'])}")
        print(f"✅ Literature quality: {result['literature_quality']}\n")
        
        return result


# Test
if __name__ == "__main__":
    hunter = CitationHunter()
    
    test_title = "Effects of mindfulness meditation on anxiety and depression"
    test_abstract = """
    This randomized controlled trial examined the effects of an 8-week mindfulness 
    meditation program on anxiety and depression symptoms in adults. Results showed 
    significant reductions in both anxiety (d=0.95) and depression (d=0.82) compared 
    to waitlist control, with effects maintained at 3-month follow-up.
    """
    
    result = hunter.analyze(test_title, test_abstract)
    
    print("\n" + "="*50)
    print("CITATION ANALYSIS:")
    print("="*50)
    print(json.dumps(result, indent=2))