from openai import AzureOpenAI
from dotenv import load_dotenv
import os
import json
import base64
import io
import fitz  # PyMuPDF
from PIL import Image

load_dotenv()


class DataVisualizationCritic:
    """Agent 7: Analyzes data visualizations against best practices (Tufte, Cleveland, Few)"""

    MAX_IMAGE_DIMENSION = 1024
    MIN_IMAGE_DIMENSION = 50
    MAX_FIGURES = 20

    def __init__(self):
        self.client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION")
        )
        self.model = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

        self.figure_prompt = """You are an expert data visualization critic specializing in scientific figures.
You evaluate figures against best practices from Edward Tufte, William Cleveland, and Stephen Few.

Analyze the provided figure image and evaluate it on these 7 criteria:

1. CHART TYPE: Identify the type (bar, line, scatter, pie, table, diagram, heatmap,
   box_plot, histogram, forest_plot, kaplan_meier, flowchart, other).
   Is this the right chart type for the data shown? If not, suggest a better alternative.
   Note: For tables, diagrams, and flowcharts, some criteria below may not apply — score them as N/A where appropriate.

2. COLOR USAGE (score 1-5):
   - Is color meaningful (encoding data) or just decorative?
   - Could a colorblind person read this? (red-green only = bad)
   - Are there too many colors reducing clarity?
   - Is there sufficient contrast?

3. AXIS ASSESSMENT (score 1-5):
   - Are axes clearly labeled with units?
   - Is the scale appropriate and not misleading?
   - For bar charts: does it start at zero? (Tufte principle)
   - Are tick marks sensible?
   - If no axes (e.g., table, diagram): score null

4. DATA-INK RATIO / Tufte (score 1-5):
   - Is there chart junk? (unnecessary gridlines, decorative borders, background fills)
   - Are unnecessary 3D effects used?
   - Could elements be removed without losing information?
   - Is the figure clean and focused?

5. LEGEND ASSESSMENT (score 1-5):
   - Is a legend present when needed?
   - Is it well-placed (not overlapping data)?
   - Are all symbols/colors explained?
   - If no legend needed: score null

6. STATISTICAL ELEMENTS:
   - Are error bars present where appropriate?
   - Is sample size indicated?
   - Is statistical significance shown (p-values, stars)?

7. CAPTION QUALITY (score 1-5):
   - Note: The caption may or may not be visible in the image.
   - If visible: Is it descriptive? Could you understand the figure without reading the paper?
   - If not visible: set score to null

For OVERALL assessment:
- Score 1-5 (average of applicable criteria)
- List 1-3 strengths
- List 1-3 specific improvements
- Priority: "critical" (major issues misleading readers), "important" (clear improvements needed), "minor" (polish/best practice)

Return valid JSON:
{
    "chart_type_detected": "bar",
    "chart_type_appropriate": true,
    "chart_type_suggestion": null,
    "color_assessment": {"score": 4, "colorblind_friendly": true, "issues": [], "suggestions": []},
    "axis_assessment": {"score": 3, "labels_clear": true, "scale_appropriate": true, "zero_baseline": false, "issues": [], "suggestions": []},
    "data_ink_ratio": {"score": 4, "chart_junk_present": false, "unnecessary_3d": false, "issues": []},
    "legend_assessment": {"score": 5, "present": true, "issues": []},
    "statistical_elements": {"error_bars_present": false, "sample_size_shown": false, "significance_indicated": false, "issues": []},
    "caption_quality": {"score": null, "descriptive": null, "standalone": null, "issues": []},
    "overall_figure_score": 4,
    "strengths": ["Clear layout"],
    "improvements": ["Add error bars"],
    "priority": "important"
}

IMPORTANT:
- Be specific and constructive — give actionable improvement suggestions
- Use null for scores that don't apply (e.g., axes for tables, legend for simple charts)
- Be honest but fair — acknowledge what works well"""

        self.caption_prompt = """You are an expert in scientific writing and figure presentation.

Analyze how figures and tables are referenced and captioned in this research paper text.

Check for:
1. Figure/table references: Find all mentions (e.g., "Figure 1", "Fig. 2", "Table 3", "Supplementary Figure S1")
2. Reference quality: Does the text describe what each figure shows, or just say "see Figure 1"?
3. Orphan figures: Are there figures mentioned in captions but never referenced in the body text?
4. Dangling references: Does the text reference figures that don't seem to exist?
5. Caption texts: Extract any figure/table captions you find in the text
6. Caption quality: Are captions descriptive, self-contained, and include key statistical info?

Return valid JSON:
{
    "figure_references_found": ["Figure 1", "Figure 2", "Table 1"],
    "total_references": 5,
    "caption_texts_found": [
        {"figure_id": "Figure 1", "caption_snippet": "first 100 chars...", "quality_score": 4}
    ],
    "orphan_figures": [],
    "dangling_references": [],
    "reference_quality": "good",
    "reference_quality_reasoning": "All figures are discussed in context with specific data points mentioned",
    "common_issues": []
}"""

        self.synthesis_prompt = """You are a data visualization expert providing a holistic assessment
of all figures in a research paper.

Given the per-figure analyses and caption analysis, provide:

1. overall_quality: Average score (1-5) across all figures, rounded to 1 decimal
2. overall_assessment: 2-3 sentence summary of the paper's visual presentation quality
3. common_patterns: Patterns you see across multiple figures (good or bad)
4. best_practice_violations: Specific Tufte/Cleveland/Few violations found
5. strengths: What the paper does well visually
6. recommendations: Top 3-5 actionable improvements, ordered by impact
7. visualization_strategy: Brief strategic advice for improving the paper's visual communication

Return valid JSON:
{
    "overall_quality": 3.5,
    "overall_assessment": "...",
    "common_patterns": [],
    "best_practice_violations": [],
    "strengths": [],
    "recommendations": [],
    "visualization_strategy": "..."
}"""

    # --- Image Extraction ---

    def _extract_figures(self, pdf_path):
        """Extract figure images from PDF using PyMuPDF"""
        figures = []
        seen_xrefs = set()

        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            print(f"   ⚠️  Could not open PDF for image extraction: {e}")
            return figures

        for page_num in range(len(doc)):
            page = doc[page_num]
            try:
                images = page.get_images(full=True)
            except Exception:
                continue

            for img_info in images:
                xref = img_info[0]

                # Deduplicate
                if xref in seen_xrefs:
                    continue
                seen_xrefs.add(xref)

                try:
                    img_data = doc.extract_image(xref)
                    if not img_data:
                        continue

                    width = img_data.get("width", 0)
                    height = img_data.get("height", 0)
                    ext = img_data.get("ext", "png")
                    image_bytes = img_data.get("image")

                    if not image_bytes:
                        continue

                    # Filter tiny images (icons, logos)
                    if width < self.MIN_IMAGE_DIMENSION or height < self.MIN_IMAGE_DIMENSION:
                        continue

                    # Filter extreme aspect ratios (line separators)
                    aspect = max(width, height) / max(min(width, height), 1)
                    if aspect > 10:
                        continue

                    # Resize if needed
                    image_bytes, ext = self._resize_if_needed(image_bytes, ext)

                    # Convert to base64
                    b64_data = base64.b64encode(image_bytes).decode("utf-8")
                    mime_type = f"image/{'jpeg' if ext in ('jpg', 'jpeg') else 'png'}"

                    figures.append({
                        "page": page_num + 1,
                        "xref": xref,
                        "base64_data": b64_data,
                        "mime_type": mime_type,
                        "width": width,
                        "height": height
                    })

                    if len(figures) >= self.MAX_FIGURES:
                        print(f"   ℹ️  Reached max figure limit ({self.MAX_FIGURES}), stopping extraction")
                        doc.close()
                        return figures

                except Exception as e:
                    print(f"   ⚠️  Failed to extract image xref={xref}: {e}")
                    continue

        doc.close()
        return figures

    def _resize_if_needed(self, image_bytes, ext):
        """Resize image if either dimension exceeds MAX_IMAGE_DIMENSION"""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            w, h = img.size

            if max(w, h) <= self.MAX_IMAGE_DIMENSION:
                return image_bytes, ext

            ratio = self.MAX_IMAGE_DIMENSION / max(w, h)
            new_w, new_h = int(w * ratio), int(h * ratio)
            img = img.resize((new_w, new_h), Image.LANCZOS)

            buffer = io.BytesIO()
            save_format = "JPEG" if ext in ("jpg", "jpeg") else "PNG"
            if img.mode == "RGBA" and save_format == "JPEG":
                img = img.convert("RGB")
            img.save(buffer, format=save_format)
            return buffer.getvalue(), ext
        except Exception:
            return image_bytes, ext

    # --- Vision Analysis ---

    def _analyze_single_figure(self, figure_data, figure_number):
        """Analyze a single figure using GPT-4.1 Vision"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.figure_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Analyze this figure (Figure {figure_number}, found on page {figure_data['page']} of the paper). Evaluate it against data visualization best practices."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{figure_data['mime_type']};base64,{figure_data['base64_data']}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=2000
        )

        result = json.loads(response.choices[0].message.content)
        result["figure_number"] = figure_number
        result["page"] = figure_data["page"]
        return result

    # --- Text Analysis ---

    def _analyze_captions(self, full_text, results_section):
        """Analyze figure captions and references in the paper text"""
        text_input = f"FULL TEXT (first 25000 chars):\n{full_text[:25000]}"
        if results_section:
            text_input += f"\n\nRESULTS SECTION:\n{results_section[:8000]}"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.caption_prompt},
                    {"role": "user", "content": text_input}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"   ⚠️  Caption analysis failed: {e}")
            return {
                "figure_references_found": [],
                "total_references": 0,
                "caption_texts_found": [],
                "orphan_figures": [],
                "dangling_references": [],
                "reference_quality": "unknown",
                "reference_quality_reasoning": f"Analysis failed: {e}",
                "common_issues": []
            }

    # --- Synthesis ---

    def _merge_caption_data(self, figure_analyses, caption_analysis):
        """Enrich figure analyses with caption quality from text analysis"""
        caption_map = {}
        for cap in caption_analysis.get("caption_texts_found", []):
            fig_id = cap.get("figure_id", "").lower().replace(".", "").strip()
            caption_map[fig_id] = cap

        for fig in figure_analyses:
            fig_num = fig.get("figure_number", 0)
            # Try matching "figure 1", "fig 1" etc.
            for key_pattern in [f"figure {fig_num}", f"fig {fig_num}", f"figure{fig_num}"]:
                if key_pattern in caption_map:
                    cap_data = caption_map[key_pattern]
                    if fig.get("caption_quality", {}).get("score") is None:
                        fig["caption_quality"] = {
                            "score": cap_data.get("quality_score"),
                            "descriptive": cap_data.get("quality_score", 0) >= 3 if cap_data.get("quality_score") else None,
                            "standalone": None,
                            "issues": []
                        }
                    break

    def _synthesize_results(self, figure_analyses, caption_analysis):
        """Synthesize per-figure analyses into overall assessment"""
        # Compute average score
        scores = [f.get("overall_figure_score") for f in figure_analyses
                  if isinstance(f.get("overall_figure_score"), (int, float))]
        avg_score = round(sum(scores) / len(scores), 1) if scores else "N/A"

        # Build summary for LLM
        figure_summaries = []
        for fig in figure_analyses:
            summary = {
                "figure_number": fig.get("figure_number"),
                "page": fig.get("page"),
                "chart_type": fig.get("chart_type_detected"),
                "overall_score": fig.get("overall_figure_score"),
                "priority": fig.get("priority"),
                "strengths": fig.get("strengths", []),
                "improvements": fig.get("improvements", []),
                "color_score": fig.get("color_assessment", {}).get("score"),
                "axis_score": fig.get("axis_assessment", {}).get("score"),
                "data_ink_score": fig.get("data_ink_ratio", {}).get("score"),
                "colorblind_friendly": fig.get("color_assessment", {}).get("colorblind_friendly"),
                "chart_junk": fig.get("data_ink_ratio", {}).get("chart_junk_present"),
            }
            figure_summaries.append(summary)

        prompt = f"""PER-FIGURE ANALYSES ({len(figure_analyses)} figures):
{json.dumps(figure_summaries, indent=2)}

CAPTION ANALYSIS:
- References found: {caption_analysis.get('total_references', 0)}
- Reference quality: {caption_analysis.get('reference_quality', 'unknown')}
- Orphan figures: {caption_analysis.get('orphan_figures', [])}
- Dangling references: {caption_analysis.get('dangling_references', [])}
- Common issues: {caption_analysis.get('common_issues', [])}

Average figure score: {avg_score}/5

Provide your holistic assessment."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.synthesis_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.4
            )
            synthesis = json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"   ⚠️  Synthesis failed: {e}")
            synthesis = {
                "overall_quality": avg_score,
                "overall_assessment": f"Analyzed {len(figure_analyses)} figures. Could not generate holistic assessment.",
                "common_patterns": [],
                "best_practice_violations": [],
                "strengths": [],
                "recommendations": [],
                "visualization_strategy": "Review individual figure feedback for specific improvements."
            }

        # Assemble final result
        result = {
            "figures_analyzed": len(figure_analyses),
            "overall_quality": synthesis.get("overall_quality", avg_score),
            "overall_assessment": synthesis.get("overall_assessment", ""),
            "figures": figure_analyses,
            "common_patterns": synthesis.get("common_patterns", []),
            "best_practice_violations": synthesis.get("best_practice_violations", []),
            "strengths": synthesis.get("strengths", []),
            "recommendations": synthesis.get("recommendations", []),
            "visualization_strategy": synthesis.get("visualization_strategy", ""),
            "caption_analysis": {
                "references_found": caption_analysis.get("total_references", 0),
                "reference_quality": caption_analysis.get("reference_quality", "unknown"),
                "orphan_figures": caption_analysis.get("orphan_figures", []),
                "dangling_references": caption_analysis.get("dangling_references", [])
            }
        }
        return result

    # --- Helpers ---

    def _empty_analysis(self, note="No figures or charts found in this PDF."):
        """Return empty analysis when no figures found"""
        return {
            "figures_analyzed": 0,
            "overall_quality": "N/A",
            "overall_assessment": note,
            "figures": [],
            "common_patterns": [],
            "best_practice_violations": [],
            "strengths": [],
            "recommendations": ["Consider adding visualizations to improve data communication"],
            "visualization_strategy": "No figures detected. Adding clear, well-designed charts could strengthen the paper's impact.",
            "caption_analysis": {
                "references_found": 0,
                "reference_quality": "N/A",
                "orphan_figures": [],
                "dangling_references": []
            }
        }

    def _failed_figure_analysis(self, figure_number, page, error):
        """Return skeleton for a figure that failed analysis"""
        return {
            "figure_number": figure_number,
            "page": page,
            "chart_type_detected": "unknown",
            "chart_type_appropriate": None,
            "chart_type_suggestion": None,
            "color_assessment": {"score": None, "colorblind_friendly": None, "issues": [f"Analysis failed: {error}"], "suggestions": []},
            "axis_assessment": {"score": None, "labels_clear": None, "scale_appropriate": None, "zero_baseline": None, "issues": [f"Analysis failed: {error}"], "suggestions": []},
            "data_ink_ratio": {"score": None, "chart_junk_present": None, "unnecessary_3d": None, "issues": [f"Analysis failed: {error}"]},
            "legend_assessment": {"score": None, "present": None, "issues": [f"Analysis failed: {error}"]},
            "statistical_elements": {"error_bars_present": None, "sample_size_shown": None, "significance_indicated": None, "issues": [f"Analysis failed: {error}"]},
            "caption_quality": {"score": None, "descriptive": None, "standalone": None, "issues": [f"Analysis failed: {error}"]},
            "overall_figure_score": None,
            "strengths": [],
            "improvements": [f"Could not analyze: {error}"],
            "priority": "minor"
        }

    # --- Main Method ---

    def analyze(self, pdf_path, full_text, results_section=""):
        """Analyze data visualizations in a research paper"""

        print("📈 Agent 7 (DataViz Critic) analyzing figures...\n")

        # Step 1: Extract figures from PDF
        print("   Extracting figures from PDF...")
        figures = self._extract_figures(pdf_path)
        print(f"   Found {len(figures)} figures\n")

        if not figures:
            print("   ℹ️  No figures found in this paper\n")
            # Still do caption analysis to check for dangling references
            caption_analysis = self._analyze_captions(full_text, results_section)
            result = self._empty_analysis()
            result["caption_analysis"]["references_found"] = caption_analysis.get("total_references", 0)
            result["caption_analysis"]["dangling_references"] = caption_analysis.get("dangling_references", [])
            return result

        # Step 2: Analyze each figure with Vision API
        figure_analyses = []
        for i, fig in enumerate(figures):
            print(f"   [{i+1}/{len(figures)}] Analyzing figure on page {fig['page']}...")
            try:
                analysis = self._analyze_single_figure(fig, i + 1)
                figure_analyses.append(analysis)
            except Exception as e:
                print(f"   ⚠️  Failed to analyze figure {i+1}: {e}")
                figure_analyses.append(self._failed_figure_analysis(i + 1, fig["page"], str(e)))

        # Step 3: Text-based caption and reference analysis
        print(f"\n   Analyzing figure captions and references in text...")
        caption_analysis = self._analyze_captions(full_text, results_section)

        # Step 4: Merge caption data into figure analyses
        self._merge_caption_data(figure_analyses, caption_analysis)

        # Step 5: Synthesize overall assessment
        print("   Generating overall assessment...")
        result = self._synthesize_results(figure_analyses, caption_analysis)

        # Print summary
        quality = result.get("overall_quality", "N/A")
        violations = len(result.get("best_practice_violations", []))
        recs = len(result.get("recommendations", []))

        print(f"\n   ✅ Figures analyzed: {result['figures_analyzed']}")
        print(f"   ✅ Overall quality: {quality}/5")
        print(f"   ✅ Best practice violations: {violations}")
        print(f"   ✅ Recommendations: {recs}\n")

        return result


# Test
if __name__ == "__main__":
    import glob

    # Find a test PDF
    pdfs = glob.glob("*.pdf")
    if not pdfs:
        pdfs = glob.glob("papers/*.pdf")

    if not pdfs:
        print("No PDF files found for testing. Place a PDF in the project directory.")
    else:
        test_pdf = pdfs[0]
        print(f"Testing with: {test_pdf}\n")

        critic = DataVisualizationCritic()

        # Quick text extraction for caption analysis
        from pypdf import PdfReader
        reader = PdfReader(test_pdf)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text()

        result = critic.analyze(test_pdf, full_text)

        print("\n" + "=" * 50)
        print("DATAVIZ ANALYSIS:")
        print("=" * 50)
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
