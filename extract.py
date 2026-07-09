"""
The two core LLM operations:
  summarize(note)  -> plain-language summary (a normal completion)
  extract(note)    -> HomeVisitExtraction object (structured output, schema-enforced)

The whole "AI" of this project is these ~30 lines. Everything else is plumbing.
"""
from config import client, CHAT_MODEL
from schema import HomeVisitExtraction

SUMMARY_SYSTEM = (
    "You summarize social-work home-visit notes for researchers. "
    "Write 3-4 clear sentences in plain language. Only use facts stated in the "
    "note. Do not invent details or add advice."
)

EXTRACT_SYSTEM = (
    "You extract structured information from a social-work home-visit note. "
    "Use ONLY information present in the note. If something is not mentioned, "
    "use an empty list, 'none mentioned', or null as appropriate. Do not guess."
)


def summarize(note_text: str) -> str:
    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": SUMMARY_SYSTEM},
            {"role": "user", "content": note_text},
        ],
    )
    return resp.choices[0].message.content.strip()


def extract(note_text: str) -> HomeVisitExtraction:
    """Returns a validated HomeVisitExtraction. The API guarantees the shape."""
    resp = client.chat.completions.parse(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": EXTRACT_SYSTEM},
            {"role": "user", "content": note_text},
        ],
        response_format=HomeVisitExtraction,
    )
    return resp.choices[0].message.parsed


if __name__ == "__main__":
    # Quick smoke test: python extract.py data/synthetic_notes/note_01_margaret.txt
    import sys, json
    path = sys.argv[1] if len(sys.argv) > 1 else "data/synthetic_notes/note_01_margaret.txt"
    text = open(path).read()
    print("SUMMARY:\n", summarize(text), "\n")
    print("EXTRACTION:\n", json.dumps(extract(text).model_dump(), indent=2))
