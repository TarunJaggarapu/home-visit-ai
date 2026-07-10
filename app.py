"""
Streamlit UI for the Home Visit Data Analysis assistant.
Run with:  streamlit run app.py
"""
import glob
import os
import json
import pandas as pd
import streamlit as st

from extract import summarize, extract
from rag import NotesIndex, answer_question

st.set_page_config(page_title="Home Visit AI Assistant", layout="wide")
st.title("🏠 AI Assistant for Home Visit Data")
st.caption("All notes shown here are synthetic. Do not upload real patient data.")

NOTES_DIR = "data/synthetic_notes"

def check_password():
    """Simple password gate so the public URL can't spend credits freely."""
    def password_entered():
        if st.session_state["password"] == st.secrets.get("APP_PASSWORD", ""):
            st.session_state["auth_ok"] = True
            del st.session_state["password"]
        else:
            st.session_state["auth_ok"] = False

    if st.session_state.get("auth_ok"):
        return True
    st.text_input("Password", type="password", key="password", on_change=password_entered)
    if st.session_state.get("auth_ok") is False:
        st.error("Incorrect password")
    st.stop()

check_password()

# ---------- helpers ----------
def read_upload(file) -> str:
    if file.name.lower().endswith(".pdf"):
        from pypdf import PdfReader
        reader = PdfReader(file)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return file.read().decode("utf-8", errors="ignore")


def load_sample_notes() -> dict[str, str]:
    notes = {}
    for path in sorted(glob.glob(os.path.join(NOTES_DIR, "*.txt"))):
        notes[os.path.basename(path)] = open(path).read()
    return notes


@st.cache_resource(show_spinner="Building the search index...")
def build_index(docs_tuple):
    # docs_tuple is a tuple of (name, text) so it is hashable for caching
    return NotesIndex().build(list(docs_tuple))


# ---------- load notes ----------
sample_notes = load_sample_notes()

with st.sidebar:
    st.header("Notes")
    uploaded = st.file_uploader(
        "Upload notes (.txt or .pdf)", type=["txt", "pdf"], accept_multiple_files=True
    )
    use_samples = st.checkbox("Include sample synthetic notes", value=True)

all_notes: dict[str, str] = {}
if use_samples:
    all_notes.update(sample_notes)
for f in uploaded or []:
    all_notes[f.name] = read_upload(f)

if not all_notes:
    st.info("Add notes in the sidebar to begin.")
    st.stop()

tab_single, tab_ask, tab_table = st.tabs(
    ["📄 Summarize & Extract", "💬 Ask across all notes", "📊 Structured table + CSV"]
)

# ---------- Tab 1: single note ----------
with tab_single:
    name = st.selectbox("Choose a note", list(all_notes.keys()))
    note_text = all_notes[name]
    with st.expander("View raw note"):
        st.text(note_text)

    if st.button("Analyze this note", type="primary"):
        # compute once, store in session_state so downloads don't wipe it
        with st.spinner("Analyzing..."):
            st.session_state["analysis"] = {
                "name": name,
                "summary": summarize(note_text),
                "data": extract(note_text).model_dump(),
            }

    # show results if we have them (survives download-button reruns)
    if st.session_state.get("analysis", {}).get("name") == name:
        result = st.session_state["analysis"]
        data = result["data"]

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Summary")
            st.write(result["summary"])

        with col2:
            st.subheader("Extracted information")

            def show(label, value):
                if value is None or value == [] or value == "":
                    st.markdown(f"**{label}:** _not mentioned_")
                elif isinstance(value, list):
                    st.markdown(f"**{label}:**")
                    for item in value:
                        st.markdown(f"- {item}")
                else:
                    st.markdown(f"**{label}:** {value}")

            show("Age", data["age"])
            show("Living situation", data["living_situation"])
            show("Health concerns", data["health_concerns"])
            show("Medication issues", data["medication_issues"])
            show("Cognitive concerns", data["cognitive_concerns"])
            show("Mental health indicators", data["mental_health_indicators"])
            show("Daily-living independence", data["adl_independence"])
            show("Mobility aids", data["mobility_aids"])
            show("Fall risk", data["fall_risk"])
            show("Fall history", data["fall_history"])
            show("Safety concerns", data["safety_concerns"])
            show("Social isolation", data["social_isolation"])
            show("Caregiver availability", data["caregiver_availability"])
            show("Social determinants", data["social_determinants"])
            show("Referrals / services", data["referrals_or_services"])
            show("Follow-up priority", data["follow_up_priority"])
            show("Other notable", data["other_notable"])

        # ---- downloads (JSON + CSV), below both columns ----
        import json
        import pandas as pd

        json_str = json.dumps(data, indent=2)
        flat = {k: ("; ".join(map(str, v)) if isinstance(v, list) else v)
                for k, v in data.items()}
        csv_str = pd.DataFrame([{"note": result["name"], **flat}]).to_csv(index=False)

        d1, d2 = st.columns(2)
        with d1:
            st.download_button("⬇ Download JSON", json_str,
                               file_name=f"{result['name']}_extraction.json",
                               mime="application/json")
        with d2:
            st.download_button("⬇ Download CSV", csv_str,
                               file_name=f"{result['name']}_extraction.csv",
                               mime="text/csv")

# ---------- Tab 2: RAG Q&A ----------
with tab_ask:
    st.write("Ask a question and the assistant answers from the note excerpts.")
    index = build_index(tuple(all_notes.items()))
    examples = [
        "What safety concerns were mentioned across the visits?",
        "Which participants have caregiver support and which do not?",
        "What cognitive issues were observed?",
        "Who is at high risk of falling?",
    ]
    picked = st.selectbox("Example questions", ["(type your own)"] + examples)
    question = st.text_input(
        "Your question", value="" if picked == "(type your own)" else picked
    )
    if st.button("Ask") and question.strip():
        answer, hits = answer_question(index, question, k=5)
        st.markdown("### Answer")
        st.write(answer)
        with st.expander("Sources used"):
            for chunk, src, score in hits:
                st.markdown(f"**{src}** (score {score:.2f})")
                st.text(chunk[:400] + ("..." if len(chunk) > 400 else ""))

# ---------- Tab 3: structured table across all notes ----------
with tab_table:
    st.write("Extract structured fields from every note and export to CSV.")
    if st.button("Extract all notes", type="primary"):
        rows = []
        progress = st.progress(0.0)
        items = list(all_notes.items())
        for i, (name, text) in enumerate(items):
            data = extract(text).model_dump()
            # flatten list fields for a readable table
            for key, val in data.items():
                if isinstance(val, list):
                    data[key] = "; ".join(str(v) for v in val)
            data = {"note": name, **data}
            rows.append(data)
            progress.progress((i + 1) / len(items))
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
        st.download_button(
            "Download CSV",
            df.to_csv(index=False).encode("utf-8"),
            file_name="home_visit_extractions.csv",
            mime="text/csv",
        )
