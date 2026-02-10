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


class JournalRecommender:
    """Agent 5: Recommends journals for paper submission using OpenAlex data"""

    def __init__(self):
        self.model = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        self.openalex_base = "https://api.openalex.org"
        self.openalex_email = os.getenv("OPENALEX_EMAIL", "")

        self.query_extraction_prompt = """You are an expert at identifying search queries for academic literature databases.

Given a paper's title and abstract, generate exactly 3 search queries that would find similar papers published in the same types of journals. Each query should capture a different angle:

1. **Topic query**: The core subject/domain (e.g., "mindfulness meditation anxiety treatment")
2. **Method query**: The methodology or approach used (e.g., "randomized controlled trial depression intervention")
3. **Niche query**: A specific, narrow aspect unique to this paper (e.g., "8-week MBSR program clinical outcomes")

Each query should be 3-6 words. Do NOT use boolean operators. Keep them suitable for the OpenAlex works search API.

Return JSON:
{
    "queries": ["query1", "query2", "query3"]
}"""

        self.system_prompt = """You are a journal selection advisor for academic researchers.

Given a paper's title, abstract, and type, along with data about candidate journals from OpenAlex (including metrics like h-index, 2-year mean citedness, open access status, and APC costs), provide personalized journal recommendations.

Rank journals by considering:
1. **Scope fit**: How well does the journal's published content match this paper's SPECIFIC research field? Prefer field-specific journals over broad/mega-journals.
2. **Impact level**: Higher impact journals should be ranked higher when the paper quality supports it. Use 2yr_mean_citedness and h_index as key indicators.
3. **Acceptance likelihood**: Given the paper's methodology quality and evidence strength, how likely is acceptance?
4. **Practical factors**: Open access options, APC costs, publication speed

IMPORTANT ranking rules:
- PREFER specialized field-specific journals over mega-journals (e.g., prefer "Quantitative Finance" over "IEEE Access" for a finance paper)
- Mega-journals (works_count > 50000, e.g., Sustainability, IEEE Access, PLOS ONE, Electronics) should only appear as backup options, NOT as primary recommendations
- Journals marked as "source": "llm_suggested" were specifically recommended for this field - give them special consideration
- The relevance_score in the data combines impact, h-index, and frequency - use it as a starting point

Split your recommendations into:
- **Primary** (top 3-5): Best-fit SPECIALIZED journals where the paper has a realistic chance
- **Secondary** (next 3-5): Backup options - including broader journals or higher-reach targets

For each journal, assess:
- scope_fit: "excellent" / "good" / "moderate"
- acceptance_likelihood: "high" / "medium" / "low"
- fit_reasoning: 1-2 sentences explaining WHY this journal fits

Also provide:
- publication_strategy: Brief strategic advice (e.g., "Submit to Journal X first; if rejected, try Y because...")
- key_strengths_for_submission: What makes this paper attractive to editors
- potential_concerns_for_reviewers: What reviewers might flag

Return JSON:
{
    "primary_recommendations": [
        {
            "journal_name": "Full Journal Name",
            "publisher": "Publisher Name",
            "impact_factor_2yr": float or null,
            "h_index": int or null,
            "is_open_access": true/false,
            "apc_usd": int or null,
            "homepage_url": "url or null",
            "issn": "ISSN or null",
            "scope_fit": "excellent/good/moderate",
            "fit_reasoning": "Why this journal fits this paper",
            "acceptance_likelihood": "high/medium/low",
            "similar_papers_found": int
        }
    ],
    "secondary_recommendations": [],
    "publication_strategy": "Strategic advice for submission order",
    "key_strengths_for_submission": ["strength1", "strength2"],
    "potential_concerns_for_reviewers": ["concern1", "concern2"],
    "recommendation_confidence": "high/medium/low"
}"""

    # --- OpenAlex API Methods ---

    def _openalex_request(self, endpoint, params=None):
        """Make a request to OpenAlex API with retry on rate limit"""
        url = f"{self.openalex_base}{endpoint}"

        if params is None:
            params = {}

        if self.openalex_email:
            params["mailto"] = self.openalex_email

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params, timeout=15)

                if response.status_code == 429:
                    wait_time = 2 ** (attempt + 1)
                    print(f"   ⚠️  Rate limited by OpenAlex, retrying in {wait_time}s... ({attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                return response.json()

            except requests.exceptions.HTTPError as e:
                if "429" not in str(e):
                    print(f"   ⚠️  OpenAlex API error: {e}")
                    return None
            except Exception as e:
                print(f"   ⚠️  OpenAlex API error: {e}")
                return None

        print("   ⚠️  OpenAlex API: rate limit exceeded after retries")
        return None

    def _search_works(self, query, per_page=50):
        """Search OpenAlex for works matching query, return source IDs with counts"""
        data = self._openalex_request("/works", params={
            "search": query,
            "per_page": per_page,
            "select": "id,display_name,primary_location"
        })

        if not data or "results" not in data:
            return {}

        source_counts = {}
        for work in data["results"]:
            primary_loc = work.get("primary_location")
            if not primary_loc:
                continue
            source = primary_loc.get("source")
            if not source or not source.get("id"):
                continue

            source_id = source["id"]
            source_name = source.get("display_name", "Unknown")

            if source_id not in source_counts:
                source_counts[source_id] = {
                    "id": source_id,
                    "name": source_name,
                    "count": 0
                }
            source_counts[source_id]["count"] += 1

        return source_counts

    def _get_source_details(self, source_id):
        """Fetch detailed journal/source info from OpenAlex"""
        short_id = source_id.split("/")[-1]

        data = self._openalex_request(f"/sources/{short_id}", params={
            "select": "id,display_name,host_organization_name,issn,is_oa,"
                      "apc_usd,homepage_url,summary_stats,works_count,"
                      "cited_by_count,type"
        })

        if not data:
            return None

        summary = data.get("summary_stats", {})

        return {
            "display_name": data.get("display_name", "Unknown"),
            "publisher": data.get("host_organization_name", "Unknown"),
            "issn": data.get("issn", [None])[0] if data.get("issn") else None,
            "is_oa": data.get("is_oa", False),
            "apc_usd": data.get("apc_usd"),
            "homepage_url": data.get("homepage_url"),
            "h_index": summary.get("h_index"),
            "impact_factor_2yr": summary.get("2yr_mean_citedness"),
            "works_count": data.get("works_count", 0),
            "cited_by_count": data.get("cited_by_count", 0),
            "type": data.get("type", "unknown")
        }

    def _search_source_by_name(self, journal_name):
        """Search OpenAlex for a specific journal by name, return best match"""
        data = self._openalex_request("/sources", params={
            "search": journal_name,
            "per_page": 3,
            "select": "id,display_name,host_organization_name,issn,is_oa,"
                      "apc_usd,homepage_url,summary_stats,works_count,"
                      "cited_by_count,type"
        })

        if not data or "results" not in data or not data["results"]:
            return None

        # Take the first (best) match
        source = data["results"][0]
        summary = source.get("summary_stats", {})

        return {
            "id": source.get("id"),
            "display_name": source.get("display_name", "Unknown"),
            "publisher": source.get("host_organization_name", "Unknown"),
            "issn": source.get("issn", [None])[0] if source.get("issn") else None,
            "is_oa": source.get("is_oa", False),
            "apc_usd": source.get("apc_usd"),
            "homepage_url": source.get("homepage_url"),
            "h_index": summary.get("h_index"),
            "impact_factor_2yr": summary.get("2yr_mean_citedness"),
            "works_count": source.get("works_count", 0),
            "cited_by_count": source.get("cited_by_count", 0),
            "type": source.get("type", "unknown")
        }

    def _suggest_journal_names(self, title, abstract):
        """Ask LLM to suggest specific field-relevant journal names"""
        prompt = f"""Paper Title: {title}

Abstract: {abstract[:1500]}

Based on this paper's specific research field and topic, suggest 8 academic journals that are well-known
in this exact domain and would be appropriate targets for submission. Focus on:
- Field-specific journals (not mega-journals like IEEE Access, Sustainability, PLOS ONE)
- Journals known for publishing this type of research
- Mix of high-impact and moderate-impact options

Return JSON:
{{
    "suggested_journals": ["Journal Name 1", "Journal Name 2", "..."]
}}"""

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert academic advisor who knows the journal landscape across all research fields."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.4
            )
            result = json.loads(response.choices[0].message.content)
            return result.get("suggested_journals", [])[:8]
        except Exception as e:
            print(f"   ⚠️  Journal suggestion failed: {e}")
            return []

    def _compute_relevance_score(self, journal):
        """Compute composite relevance score: frequency + impact + h-index"""
        freq = journal.get("similar_papers_found", 0)
        impact = journal.get("impact_factor_2yr") or 0
        h_index = journal.get("h_index") or 0

        # Weighted composite: impact matters most, then h-index, then frequency
        score = (impact * 3.0) + (h_index * 0.1) + (freq * 2.0)
        return score

    # --- Core Methods ---

    def _extract_search_queries(self, title, abstract):
        """Use LLM to extract 3 search queries from paper title + abstract"""
        prompt = f"""Paper Title: {title}

Abstract: {abstract[:2000]}

Generate 3 search queries to find similar papers in academic databases."""

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.query_extraction_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.4
            )
            result = json.loads(response.choices[0].message.content)
            return result.get("queries", [title])[:3]
        except Exception as e:
            print(f"   ⚠️  Query extraction failed: {e}")
            return [" ".join(title.split()[:5])]

    def _rank_journals(self, title, abstract, paper_type, methods_quality,
                       evidence_strength, journal_details):
        """Use LLM to rank and recommend journals based on collected data"""

        journals_text = json.dumps(journal_details, indent=2)

        quality_context = f"paper_type: {paper_type}\n"
        if methods_quality is not None:
            quality_context += f"methods_quality: {methods_quality}/5\n"
        else:
            quality_context += "methods_quality: N/A (review paper or not assessed)\n"
        if evidence_strength:
            quality_context += f"evidence_strength: {evidence_strength}\n"
        else:
            quality_context += "evidence_strength: not assessed\n"

        prompt = f"""PAPER TO SUBMIT:
Title: {title}
Abstract: {abstract[:2000]}

PAPER QUALITY CONTEXT:
{quality_context}

CANDIDATE JOURNALS (from OpenAlex, sorted by composite relevance score combining impact, h-index, and frequency):
{journals_text}

Note: Journals with "source": "llm_suggested" were specifically recommended for this research field.
Journals with "source": "frequency" were found by searching for similar papers.
Prefer specialized field-specific journals as primary recommendations.

Based on the paper's content, quality, and the journal data above, provide your ranked recommendations.
Ensure impact_factor_2yr, h_index, is_open_access, apc_usd, homepage_url, and issn in each recommendation
match the data provided. Fill in publisher from the data. Set similar_papers_found from the data."""

        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.4
        )

        return json.loads(response.choices[0].message.content)

    def _llm_only_fallback(self, title, abstract, paper_type,
                           methods_quality, evidence_strength):
        """Fallback: recommend journals using LLM knowledge only (no grounding data)"""

        print("   Using LLM-only recommendations (no OpenAlex grounding)...\n")

        quality_context = f"paper_type: {paper_type}\n"
        if methods_quality is not None:
            quality_context += f"methods_quality: {methods_quality}/5\n"
        if evidence_strength:
            quality_context += f"evidence_strength: {evidence_strength}\n"

        prompt = f"""PAPER TO SUBMIT:
Title: {title}
Abstract: {abstract[:2000]}

PAPER QUALITY CONTEXT:
{quality_context}

NOTE: I could not retrieve journal data from OpenAlex. Based on your knowledge of academic journals,
provide your best recommendations. Set impact_factor_2yr, h_index, apc_usd, homepage_url, and issn
to null for any values you are not certain about. Set similar_papers_found to 0 for all.

Provide your ranked recommendations."""

        try:
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
        except Exception as e:
            print(f"   ⚠️  LLM fallback also failed: {e}")
            result = self._empty_recommendations()

        result["recommendation_confidence"] = "low"
        result["search_queries_used"] = []
        result["journals_found"] = 0

        print(f"✅ Primary recommendations: {len(result.get('primary_recommendations', []))}")
        print(f"✅ Secondary recommendations: {len(result.get('secondary_recommendations', []))}")
        print(f"✅ Confidence: low (no OpenAlex data)\n")

        return result

    def _empty_recommendations(self):
        """Return empty structure when everything fails"""
        return {
            "search_queries_used": [],
            "journals_found": 0,
            "primary_recommendations": [],
            "secondary_recommendations": [],
            "publication_strategy": "Unable to generate recommendations. Please consult journal selection tools like Jane (https://jane.biosemantics.org/) or Elsevier Journal Finder.",
            "key_strengths_for_submission": [],
            "potential_concerns_for_reviewers": [],
            "recommendation_confidence": "low"
        }

    # --- Main Method ---

    def analyze(self, paper_title, paper_abstract, paper_type="original_research",
                methods_quality=None, evidence_strength=None):
        """Recommend journals for paper submission"""

        print("📚 Agent 5 (Journal Recommender) searching journals...\n")

        # Step 1: Extract search queries via LLM
        print("   Generating search queries...")
        queries = self._extract_search_queries(paper_title, paper_abstract)
        print(f"   Queries: {queries}\n")

        # Step 2a: Search OpenAlex for similar works (frequency-based)
        print("   Searching OpenAlex for similar papers...")
        all_sources = {}
        for i, query in enumerate(queries):
            print(f"   [{i+1}/3] Searching: '{query}'")
            source_counts = self._search_works(query, per_page=50)
            for sid, info in source_counts.items():
                if sid in all_sources:
                    all_sources[sid]["count"] += info["count"]
                else:
                    all_sources[sid] = info.copy()
            time.sleep(0.2)

        # Step 2b: LLM suggests field-specific journals → verify in OpenAlex
        print("\n   Asking LLM for field-specific journal suggestions...")
        suggested_names = self._suggest_journal_names(paper_title, paper_abstract)
        llm_journals = {}
        if suggested_names:
            print(f"   LLM suggested: {suggested_names}")
            for name in suggested_names:
                source = self._search_source_by_name(name)
                if source and source.get("id"):
                    sid = source["id"]
                    if sid not in all_sources and sid not in llm_journals:
                        llm_journals[sid] = {
                            "id": sid,
                            "name": source["display_name"],
                            "count": 0,
                            "llm_suggested": True
                        }
                time.sleep(0.15)
            print(f"   Verified {len(llm_journals)} new journals in OpenAlex\n")

        if not all_sources and not llm_journals:
            print("   ⚠️  No journals found, falling back to LLM-only...\n")
            return self._llm_only_fallback(paper_title, paper_abstract, paper_type,
                                           methods_quality, evidence_strength)

        # Step 3: Fetch details for top frequency-based + all LLM-suggested
        sorted_sources = sorted(all_sources.values(), key=lambda x: x["count"], reverse=True)
        top_freq_sources = sorted_sources[:12]

        # Combine: top 12 by frequency + all LLM-suggested (deduplicated)
        sources_to_fetch = {s["id"]: s for s in top_freq_sources}
        for sid, info in llm_journals.items():
            if sid not in sources_to_fetch:
                sources_to_fetch[sid] = info
        print(f"   Fetching details for {len(sources_to_fetch)} journals ({len(top_freq_sources)} frequency + {len(llm_journals)} LLM-suggested)...")

        # Step 4: Fetch journal details + compute composite score
        journal_details = []
        for source in sources_to_fetch.values():
            details = self._get_source_details(source["id"])
            if details:
                details["similar_papers_found"] = source.get("count", 0)
                details["source"] = "llm_suggested" if source.get("llm_suggested") else "frequency"
                details["relevance_score"] = self._compute_relevance_score(details)
                journal_details.append(details)
            time.sleep(0.15)

        if not journal_details:
            print("   ⚠️  Could not fetch journal details, falling back to LLM-only...\n")
            return self._llm_only_fallback(paper_title, paper_abstract, paper_type,
                                           methods_quality, evidence_strength)

        # Sort by composite relevance score (impact + h-index + frequency)
        journal_details.sort(key=lambda x: x["relevance_score"], reverse=True)
        journal_details = journal_details[:20]  # Top 20 for LLM ranking

        print(f"   Retrieved details for {len(journal_details)} journals (sorted by relevance score)\n")

        # Step 5: LLM-powered personalized ranking
        print("   Generating personalized recommendations...")
        result = self._rank_journals(paper_title, paper_abstract, paper_type,
                                     methods_quality, evidence_strength, journal_details)

        result["search_queries_used"] = queries
        result["journals_found"] = len(journal_details)

        print(f"\n✅ Primary recommendations: {len(result.get('primary_recommendations', []))}")
        print(f"✅ Secondary recommendations: {len(result.get('secondary_recommendations', []))}")
        print(f"✅ Confidence: {result.get('recommendation_confidence', 'unknown')}\n")

        return result


# Test
if __name__ == "__main__":
    recommender = JournalRecommender()

    test_title = "Effects of mindfulness meditation on anxiety and depression"
    test_abstract = """
    This randomized controlled trial examined the effects of an 8-week mindfulness
    meditation program on anxiety and depression symptoms in adults. Results showed
    significant reductions in both anxiety (d=0.95) and depression (d=0.82) compared
    to waitlist control, with effects maintained at 3-month follow-up.
    """

    result = recommender.analyze(
        test_title, test_abstract,
        paper_type="original_research",
        methods_quality=4,
        evidence_strength="strong"
    )

    print("\n" + "="*50)
    print("JOURNAL RECOMMENDATIONS:")
    print("="*50)
    print(json.dumps(result, indent=2))
