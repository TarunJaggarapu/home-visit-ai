# AI Assistant for Home Visit Data Analysis

An LLM-powered tool that helps social-work researchers analyze unstructured home-visit
notes. It **summarizes** visits, **extracts** structured fields (age, living situation,
health concerns, caregiver availability, fall risk, medication issues, cognitive concerns,
safety concerns), lets researchers **ask questions across all notes** using
retrieval-augmented generation (RAG), and **exports** the structured data to CSV.

> ⚠️ **Ethics note:** All notes in `data/synthetic_notes/` are synthetic (AI-generated /
> hand-written examples). This project must **never** be used with real patient or
> participant data.

## What it does

- **Summarize & Extract** — pick a note, get a plain-language summary plus a
  schema-enforced JSON extraction.
- **Ask across all notes** — natural-language Q&A grounded in the notes (RAG), with the
  source excerpts shown.
- **Structured table + CSV** — run extraction over every note and download a tidy CSV.

## Tech stack

| Layer | Tool |
|---|---|
| LLM + embeddings | OpenAI (`gpt-4o-mini`, `text-embedding-3-small`) — swappable |
| Structured extraction | OpenAI Structured Outputs + Pydantic schema |
| Vector search (RAG) | FAISS |
| UI | Streamlit |
| Data | Synthetic home-visit notes |

## Project layout

```
home-visit-ai/
├── app.py         # Streamlit UI (3 tabs)
├── config.py      # model + client in one place (swap provider here)
├── schema.py      # Pydantic extraction schema (the fields to pull out)
├── extract.py     # summarize() and extract() — the core LLM calls
├── rag.py         # embeddings + FAISS index + answer_question()
├── requirements.txt
├── .env.example
└── data/synthetic_notes/   # 12 synthetic notes
```

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your API key
cp .env.example .env             # then edit .env and paste your OPENAI_API_KEY
```

Get a key at platform.openai.com. Running the 12 sample notes costs only a few cents
with `gpt-4o-mini`.

## Run

```bash
# Quick command-line test of one note:
python extract.py data/synthetic_notes/note_01_margaret.txt

# Full app:
streamlit run app.py
```

## Switching the LLM provider (optional)

Everything routes through `config.py`. To go **free / local**, install
[Ollama](https://ollama.com), `ollama pull llama3.1`, then set the client to:
`OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")` and use a local model
name. Note: local models don't support strict structured outputs as reliably, so the
extraction tab is most accurate with a hosted model.

## Known limitations

- Extraction quality depends on note wording; always spot-check against the source.
- Character-based chunking is simple by design; sentence/section chunking could improve
  retrieval on longer documents.
- Not validated for clinical use — this is a research/portfolio prototype.
