from openai import AzureOpenAI
from dotenv import load_dotenv
import os
import json
import requests
import time

load_dotenv()


class FundingAdvisor:
    """Agent 6: Identifies funding sources for research using OpenAlex data"""

    def __init__(self):
        self.client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION")
        )
        self.model = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        self.openalex_base = "https://api.openalex.org"
        self.openalex_email = os.getenv("OPENALEX_EMAIL", "")

        self.system_prompt = """You are an academic funding advisor who helps researchers identify
suitable grants, funding programs, and sponsors for their research.

Given a paper's title, abstract, and data about funders who have funded similar research
(from OpenAlex), provide personalized funding recommendations.

For each funder, provide:
- funder_name: Official name
- country: Country code (e.g., "US", "DE", "EU")
- homepage_url: Official website
- relevance: "high" / "medium" / "low" — how well this funder matches the research topic
- relevance_reasoning: 1-2 sentences explaining WHY this funder is relevant
- known_programs: List of 1-3 specific funding programs this funder offers that could fit
  (use your knowledge — e.g., "DFG Sachbeihilfe", "NIH R01", "ERC Starting Grant")
- typical_amount: Estimated typical grant amount range (e.g., "$50,000-$500,000", "€200,000-€1,500,000")
- typical_duration: Typical grant duration (e.g., "3-5 years")
- eligibility_notes: Brief notes on who can apply (e.g., "PI must be at a German university")
- application_tip: One practical tip for applying

Split recommendations into:
- **primary_funders** (top 3-5): Best-fit funders who actively fund this type of research
- **secondary_funders** (next 3-5): Additional options — regional, smaller, or more competitive

Also provide:
- funding_strategy: Brief strategic advice for seeking funding in this field
- funding_landscape: 2-3 sentences describing the overall funding landscape for this research area
- total_similar_funded_papers: How many of the analyzed papers had funding data

Return valid JSON with this structure:
{
    "primary_funders": [...],
    "secondary_funders": [...],
    "funding_strategy": "...",
    "funding_landscape": "...",
    "total_similar_funded_papers": int,
    "data_confidence": "high/medium/low"
}

IMPORTANT:
- Base your recommendations on the ACTUAL funder data provided — these are real funders who funded similar research
- Use your knowledge to enrich with program names, amounts, and tips — but mark this clearly
- If few papers had funding data, set data_confidence to "low" and note this limitation
- Be honest about limitations — you don't have live deadline data"""

    # --- OpenAlex API Methods ---

    def _openalex_request(self, endpoint, params=None):
        """Make OpenAlex API request with retry on 429"""
        url = f"{self.openalex_base}{endpoint}"
        if params is None:
            params = {}
        if self.openalex_email:
            params["mailto"] = self.openalex_email

        for attempt in range(3):
            try:
                response = requests.get(url, params=params, timeout=15)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    wait = 2 ** (attempt + 1)
                    print(f"   ⚠️  Rate limited, waiting {wait}s...")
                    time.sleep(wait)
                else:
                    return None
            except requests.exceptions.RequestException:
                time.sleep(1)
        return None

    def _search_works_for_funders(self, query, per_page=50):
        """Search OpenAlex works and extract funder information"""
        data = self._openalex_request("/works", params={
            "search": query,
            "per_page": per_page,
            "select": "id,display_name,funders,publication_year"
        })

        if not data or "results" not in data:
            return {}, 0, 0

        funder_counts = {}
        total_works = len(data["results"])
        funded_works = 0

        for work in data["results"]:
            funders = work.get("funders", [])
            if funders:
                funded_works += 1
                for funder in funders:
                    fid = funder.get("id")
                    if fid:
                        if fid not in funder_counts:
                            funder_counts[fid] = {
                                "id": fid,
                                "name": funder.get("display_name", "Unknown"),
                                "count": 0
                            }
                        funder_counts[fid]["count"] += 1

        return funder_counts, total_works, funded_works

    def _get_funder_details(self, funder_id):
        """Get detailed funder information from OpenAlex"""
        # Extract the ID part (F-prefixed)
        if "openalex.org/" in funder_id:
            short_id = funder_id.split("/")[-1]
        else:
            short_id = funder_id

        data = self._openalex_request(f"/funders/{short_id}")
        if not data:
            return None

        summary = data.get("summary_stats", {})

        return {
            "id": data.get("id"),
            "display_name": data.get("display_name", "Unknown"),
            "alternate_titles": data.get("alternate_titles", []),
            "country_code": data.get("country_code"),
            "description": data.get("description", ""),
            "homepage_url": data.get("homepage_url"),
            "awards_count": data.get("awards_count", 0),
            "works_count": data.get("works_count", 0),
            "cited_by_count": data.get("cited_by_count", 0),
            "h_index": summary.get("h_index"),
            "2yr_mean_citedness": summary.get("2yr_mean_citedness"),
            "ids": {
                "ror": data.get("ids", {}).get("ror"),
                "crossref": data.get("ids", {}).get("crossref"),
                "wikidata": data.get("ids", {}).get("wikidata")
            }
        }

    def _get_sample_awards(self, funder_id, max_results=5):
        """Get sample awards from a funder to show typical amounts"""
        short_id = funder_id.split("/")[-1] if "openalex.org/" in funder_id else funder_id

        data = self._openalex_request("/awards", params={
            "filter": f"funder.id:{short_id},amount:>0",
            "per_page": max_results,
            "sort": "amount:desc"
        })

        if not data or "results" not in data:
            return [], 0

        awards = []
        for award in data["results"]:
            awards.append({
                "display_name": award.get("display_name"),
                "amount": award.get("amount"),
                "currency": award.get("currency"),
                "funder_scheme": award.get("funder_scheme"),
                "funding_type": award.get("funding_type"),
                "start_year": award.get("start_year"),
                "end_year": award.get("end_year"),
                "lead_investigator": award.get("lead_investigator", {}).get("family_name") if award.get("lead_investigator") else None
            })

        total = data.get("meta", {}).get("count", 0)
        return awards, total

    def _extract_search_queries(self, title, abstract):
        """Use LLM to generate search queries for finding similar funded research"""
        prompt = f"""Paper Title: {title}

Abstract: {abstract[:2000]}

Generate exactly 3 search queries to find similar research papers in OpenAlex.
Each query should capture a different angle:
1. Core research topic
2. Methodology or approach
3. Specific application or niche

Return JSON:
{{
    "queries": ["query1", "query2", "query3"]
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Generate concise academic search queries. Each query should be 3-6 words."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            result = json.loads(response.choices[0].message.content)
            return result.get("queries", [title.split()[:5]])[:3]
        except Exception as e:
            print(f"   ⚠️  Query extraction failed: {e}")
            return [" ".join(title.split()[:5])]

    def _rank_funders(self, title, abstract, paper_type, funder_details, stats):
        """Use LLM to rank and enrich funder recommendations"""
        funders_text = json.dumps(funder_details, indent=2, ensure_ascii=False)

        prompt = f"""RESEARCH PAPER:
Title: {title}
Abstract: {abstract[:2000]}
Paper Type: {paper_type}

ANALYSIS STATS:
- Total similar papers searched: {stats['total_works']}
- Papers with funding data: {stats['funded_works']} ({stats['funding_rate']:.0%})

FUNDERS WHO FUNDED SIMILAR RESEARCH (from OpenAlex, sorted by frequency):
{funders_text}

Based on the paper's topic and the funder data, provide your personalized funding recommendations.
Enrich each funder with your knowledge about their specific programs, typical amounts, and eligibility.
Be honest: if the funding data coverage is low, say so."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.4
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"   ⚠️  LLM ranking failed: {e}")
            return self._empty_result()

    def _empty_result(self):
        """Return empty result structure"""
        return {
            "primary_funders": [],
            "secondary_funders": [],
            "funding_strategy": "Could not generate recommendations. Consider using ELFI (elfi.info) or GrantForward for manual search.",
            "funding_landscape": "Unable to analyze funding landscape.",
            "total_similar_funded_papers": 0,
            "data_confidence": "low",
            "search_queries_used": [],
            "funders_found": 0
        }

    # --- Main Method ---

    def analyze(self, paper_title, paper_abstract, paper_type="original_research"):
        """Analyze funding landscape for a research paper"""

        print("💰 Agent 6 (Funding Advisor) searching funding sources...\n")

        # Step 1: Extract search queries
        print("   Generating search queries...")
        queries = self._extract_search_queries(paper_title, paper_abstract)
        print(f"   Queries: {queries}\n")

        # Step 2: Search OpenAlex for similar works → extract funders
        print("   Searching OpenAlex for similar funded papers...")
        all_funders = {}
        total_works = 0
        total_funded = 0

        for i, query in enumerate(queries):
            print(f"   [{i+1}/3] Searching: '{query}'")
            funder_counts, works, funded = self._search_works_for_funders(query, per_page=50)

            total_works += works
            total_funded += funded

            for fid, info in funder_counts.items():
                if fid in all_funders:
                    all_funders[fid]["count"] += info["count"]
                else:
                    all_funders[fid] = info.copy()
            time.sleep(0.2)

        funding_rate = total_funded / total_works if total_works > 0 else 0
        print(f"\n   Found {len(all_funders)} unique funders across {total_funded}/{total_works} funded papers ({funding_rate:.0%})\n")

        if not all_funders:
            print("   ⚠️  No funders found in similar research\n")
            result = self._empty_result()
            result["search_queries_used"] = queries
            return result

        # Step 3: Get top funders by frequency
        sorted_funders = sorted(all_funders.values(), key=lambda x: x["count"], reverse=True)
        top_funders = sorted_funders[:15]

        print(f"   Top funders by frequency:")
        for f in top_funders[:5]:
            print(f"     - {f['name']}: {f['count']} papers")

        # Step 4: Fetch detailed funder info
        print(f"\n   Fetching details for top {len(top_funders)} funders...")
        funder_details = []

        for funder in top_funders:
            details = self._get_funder_details(funder["id"])
            if details:
                details["similar_papers_funded"] = funder["count"]

                # Try to get sample awards with amounts
                awards, awards_total = self._get_sample_awards(funder["id"], max_results=3)
                if awards:
                    details["sample_awards"] = awards
                    details["total_awards_with_amount"] = awards_total

                funder_details.append(details)
            time.sleep(0.15)

        print(f"   Retrieved details for {len(funder_details)} funders\n")

        if not funder_details:
            print("   ⚠️  Could not fetch funder details\n")
            result = self._empty_result()
            result["search_queries_used"] = queries
            return result

        # Step 5: LLM-powered personalized ranking
        print("   Generating personalized funding recommendations...")
        stats = {
            "total_works": total_works,
            "funded_works": total_funded,
            "funding_rate": funding_rate
        }

        result = self._rank_funders(paper_title, paper_abstract, paper_type,
                                    funder_details, stats)

        result["search_queries_used"] = queries
        result["funders_found"] = len(funder_details)

        # Print summary
        primary = result.get("primary_funders", [])
        secondary = result.get("secondary_funders", [])
        confidence = result.get("data_confidence", "unknown")

        print(f"\n   ✅ Primary Funders: {len(primary)}")
        for f in primary:
            print(f"      - {f.get('funder_name', 'Unknown')} ({f.get('country', '?')})")
        print(f"   ✅ Secondary Funders: {len(secondary)}")
        print(f"   ✅ Data Confidence: {confidence.upper()}")
        print(f"   ✅ Funded Papers Analyzed: {total_funded}/{total_works}\n")

        return result


# Test
if __name__ == "__main__":
    advisor = FundingAdvisor()
    result = advisor.analyze(
        paper_title="Machine Learning Approaches for Stock Market Prediction Using Alternative Data",
        paper_abstract="This study explores the application of machine learning algorithms including LSTM networks and gradient boosting for predicting stock market movements using alternative data sources such as sentiment analysis and satellite imagery.",
        paper_type="original_research"
    )

    print("\n" + "="*50)
    print("FUNDING RECOMMENDATIONS:")
    print("="*50)
    print(json.dumps(result, indent=2, ensure_ascii=False))
