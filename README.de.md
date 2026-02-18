# Research Paper Analyzer

> **Sprache:** [English](README.md) | Deutsch

**KI-gestützte Analyse wissenschaftlicher Forschungsarbeiten mit 8 spezialisierten Agenten.**

Laden Sie ein beliebiges Forschungspapier als PDF hoch und erhalten Sie in wenigen Minuten eine umfassende, mehrdimensionale Analyse — zu Methodik, Schreibqualität, Datenvisualisierungen, Zitaten, Plagiatrisiko, Zeitschriftenempfehlungen und Fördermöglichkeiten.

**[Live-Demo ausprobieren](https://research-paper-analyzer-2026.streamlit.app/)** — 3 voranalysierte Paper sofort verfügbar, kein Konto erforderlich.

---

## Was es leistet

Die meisten Review-Tools konzentrieren sich auf eine einzelne Dimension. Dieser Analyzer setzt **8 unabhängige KI-Agenten** ein, die jeweils auf einen anderen Aspekt der akademischen Papierbewertung spezialisiert sind. Sie laufen parallel und liefern strukturiertes, umsetzbares Feedback.

| Agent | Was er bewertet | Wichtigste Ausgabe |
|-------|-----------------|-------------------|
| **Results Synthesizer** | Zentrale Ergebnisse, Effektstärken, statistische Signifikanz | Bewertung der Evidenzstärke, p-Werte, Konfidenzintervalle |
| **Writing Coach** | Akademische Schreibqualität pro Abschnitt | Bewertung (1-5), Passivanteil %, Satzlänge, Styleguide-Referenzen |
| **Methodology Critic** | Studiendesign, Stichprobengröße, Bias, Reproduzierbarkeit | Qualitätsbewertung (1-5), identifizierte Verzerrungen, kritische Probleme |
| **DataViz Critic** | Abbildungen nach Tufte/Cleveland/Few Best Practices | Bewertung pro Abbildung, Farbenblind-Zugänglichkeit, Chart-Junk-Erkennung |
| **Citation Hunter** | Verwandte Literatur via Semantic Scholar | Unterstützende & widersprüchliche Paper, Forschungslücken |
| **Plagiarism Detector** | Fehlende Zitate, verdächtige Paraphrasierungen | Risiko-Score (0-100), markierte Abschnitte mit Schweregrad |
| **Journal Recommender** | Zielzeitschriften via OpenAlex-Metriken | 5+5 gerankte Zeitschriften mit Impact Factor, h-Index, APC, Annahmewahrscheinlichkeit |
| **Funding Advisor** | Förderquellen aus ähnlich geförderter Forschung | Gerankte Fördergeber mit Programmen, typischen Beträgen, Berechtigung, Bewerbungstipps |

### Unterstützte Paper-Typen

- Originalforschung
- Review-Artikel / Literaturübersichten
- Meta-Analysen
- Fallstudien

---

## Architektur

```
PDF Upload
    |
    v
Textextraktion (pypdf) ──> Abschnittserkennung (LLM) ──> Paper-Typ-Klassifikation
    |
    v
 [PARALLELE AUSFÜHRUNG - ThreadPoolExecutor]
 |        |         |        |        |         |         |
 v        v         v        v        v         v         v
Results  Writing  Methods  DataViz  Citations  Plagiarism  Funding
         |                                       |
         v                                       v
    (6 LLM-Aufrufe,               (PyMuPDF extrahiert Abbildungen,
     Python Regex                  GPT-4o Vision analysiert
     + LLM Hybrid)                bis zu 5 Diagramme)
                     |
                     v
              Journal Recommender
         (läuft nach Methods + Results
          für bessere Empfehlungen)
                     |
                     v
           Aggregation ──> Dashboard (9 Tabs)
                       ──> JSON Export
                       ──> Markdown Report
```

**Zentrale Designentscheidungen:**
- **Hybrider Python + LLM Ansatz** — Python berechnet objektive Metriken (Passivanteil, Satzlänge, Hedge-Word-Anzahl), LLM liefert qualitative Interpretation
- **LLM-basierte Abschnittserkennung** — Nicht regex-basiert, da akademische Paper je nach Fachgebiet stark variieren
- **Vision-basierte Abbildungsanalyse** — GPT-4o Vision bewertet die tatsächlichen Diagramm-Visualisierungen, nicht nur Textbeschreibungen
- **Paper-Typ-bewusst** — Review-Paper erhalten andere Plagiatskriterien (Paraphrasierung wird erwartet), Methodik wird anders bewertet
- **Abschnittsübergreifender Kontext** — Methodik-Agent liest Methoden + Abstract + Ergebnisse gemeinsam für eine tiefere Analyse

---

## Demo-Modus

Drei voranalysierte Paper sind für sofortige Erkundung ohne Azure-Zugangsdaten enthalten:

| Paper | Typ | Fachgebiet |
|-------|-----|------------|
| Hospital Variation in THR Outcomes (n=583) | Originalforschung | Gesundheitswesen / Orthopädie |
| Pharmacological Advances in HIV Treatment | Review-Artikel | Pharmakologie / Infektionskrankheiten |
| ML Framework for Stock Market Prediction | Originalforschung | Quantitative Finance / KI |

---

## Tech Stack

| Komponente | Technologie |
|------------|------------|
| Frontend | Streamlit |
| LLM | Azure OpenAI (GPT-4o) |
| PDF Text | pypdf |
| PDF Bilder | PyMuPDF (fitz) |
| Zitationssuche | Semantic Scholar API (kostenlos) |
| Zeitschriften- & Förderdaten | OpenAlex API (kostenlos) |
| Bildverarbeitung | Pillow |
| Parallelisierung | concurrent.futures.ThreadPoolExecutor |

---

## Kosten pro Analyse

Ausführung aller 8 Agenten für ein typisches 12-seitiges Paper:

| Agent | Kosten | Zeit |
|-------|--------|------|
| Results Synthesizer | ~$0.01 | ~5s |
| Writing Coach | ~$0.03 | ~30s |
| Methodology Critic | ~$0.02 | ~5s |
| DataViz Critic | ~$0.05-0.15 | ~60-120s |
| Citation Hunter | ~$0.02 | ~10s |
| Plagiarism Detector | ~$0.03 | ~5s |
| Journal Recommender | ~$0.04 | ~60-120s |
| Funding Advisor | ~$0.04 | ~60-120s |
| **Gesamt** | **~$0.24-0.34** | **~3-5 Min** |

Semantic Scholar und OpenAlex APIs sind kostenlos. Durch parallele Ausführung wird die Gesamtlaufzeit vom langsamsten Agenten bestimmt (~2-3 Minuten).

---

## Lokale Einrichtung

### Voraussetzungen

- Python 3.11+
- Azure OpenAI Ressource mit einem GPT-4o Deployment

### Installation

```bash
git clone https://github.com/leelesemann-sys/research-paper-analyzer.git
cd research-paper-analyzer
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### Konfiguration

Kopieren Sie `.env.example` nach `.env` und tragen Sie Ihre Azure OpenAI Zugangsdaten ein:

```
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

### Starten

```bash
streamlit run Paper_Analyzer.py
```

Der Demo-Modus funktioniert ohne Azure-Zugangsdaten — Sie können 3 voranalysierte Paper sofort erkunden.

---

## Projektstruktur

```
research-paper-analyzer/
|-- Paper_Analyzer.py          # Streamlit Frontend (Haupt-App)
|-- workflow.py                # Orchestrator: PDF-Verarbeitung, Abschnittserkennung, Agenten-Koordination
|-- agents/
|   |-- results.py             # Agent 1: Results Synthesizer
|   |-- writing.py             # Agent 2: Writing Quality Coach
|   |-- methodology.py         # Agent 3: Methodology Critic
|   |-- visualization.py       # Agent 4: DataViz Critic (Vision API)
|   |-- citations.py           # Agent 5: Citation Hunter (Semantic Scholar)
|   |-- plagiarism.py          # Agent 6: Plagiarism Detector
|   |-- journals.py            # Agent 7: Journal Recommender (OpenAlex)
|   |-- funding.py             # Agent 8: Funding Advisor (OpenAlex)
|-- pages/
|   |-- 1_How_It_Works.py      # Architektur- & Agenten-Dokumentationsseite
|-- demo_data/                 # Vorberechnete Demo-Analysen (3 Paper)
|-- requirements.txt
|-- .env.example
```

---

## Lizenz

Dieses Projekt dient Portfolio- und Bildungszwecken.

---

Erstellt mit Azure OpenAI, Streamlit, Semantic Scholar und OpenAlex.
