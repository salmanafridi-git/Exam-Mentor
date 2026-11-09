"""
Exam Mentor - Exam prep for Matric & Intermediate students
Upload a textbook chapter -> practice questions, answer checking, MCQ quizzes.
Explanations in English, Urdu (اردو) and Roman Urdu.
Powered by Google AI Studio (Gemini) API.

Run locally:  streamlit run app.py
"""

import io
import json
import re

import streamlit as st
from docx import Document
from google import genai
from google.genai import types
from pypdf import PdfReader

APP_NAME = "Exam Mentor"  # change this to rename the app everywhere
DEFAULT_MODEL = "gemini-3.5-flash"
MAX_CHARS = 60000  # chapter characters sent to the model

# ----------------------------------------------------------------------------
# Page setup & styling
# ----------------------------------------------------------------------------
st.set_page_config(page_title=APP_NAME, page_icon="📚", layout="wide")

st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu&display=swap" rel="stylesheet">
    <style>
      .urdu {
          font-family: 'Noto Nastaliq Urdu', 'Jameel Noori Nastaleeq', serif;
          direction: rtl; text-align: right; line-height: 2.4; font-size: 1.15rem;
      }
      .box { padding: 0.8rem 1rem; border-radius: 0.6rem; background: rgba(120,120,120,0.10);
             margin-bottom: 0.6rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

LANGS = {"English": "en", "اردو (Urdu)": "ur", "Roman Urdu": "roman_ur"}


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def extract_text(uploaded) -> str:
    name = uploaded.name.lower()
    data = uploaded.read()
    if name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(data))
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    if name.endswith(".docx"):
        doc = Document(io.BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs)
    return data.decode("utf-8", errors="ignore")  # .txt / .md


def get_api_key() -> str:
    try:
        key = st.secrets.get("GOOGLE_API_KEY", "")
    except Exception:
        key = ""
    return key or st.session_state.get("api_key_input", "")


def ask_llm(system: str, user: str):
    """Call Gemini and return parsed JSON."""
    key = get_api_key()
    if not key:
        st.error("Please add your Google AI Studio API key in the sidebar (or in Streamlit secrets).")
        st.stop()

    client = genai.Client(api_key=key)
    resp = client.models.generate_content(
        model=st.session_state.get("model") or DEFAULT_MODEL,
        contents=user,
        config=types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",  # forces valid JSON output
            temperature=0.4,
            max_output_tokens=16000,
        ),
    )
    return parse_json(resp.text)


def parse_json(raw: str):
    raw = (raw or "").strip()
    raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
    return json.loads(raw)


def base_system() -> str:
    level = st.session_state.get("level", "Matric")
    subject = st.session_state.get("subject", "") or "the subject"
    return (
        f"You are an expert, friendly Pakistani teacher preparing {level} students "
        f"(Punjab/Sindh/KPK/Federal board style) for exams in {subject}. "
        "Use ONLY the chapter text provided; never invent facts that are not in it. "
        "Keep the language simple and exam-oriented. "
        "When asked for Urdu, write proper Urdu in Urdu script. "
        "When asked for Roman Urdu, write Urdu using English letters "
        "(for example: 'Yeh sawal bohat aasan hai'). "
        "Respond with valid JSON only."
    )


def chapter_block() -> str:
    return f"CHAPTER TEXT:\n\"\"\"\n{st.session_state['chapter'][:MAX_CHARS]}\n\"\"\""


def show_trilingual(expl, wanted: list):
    """Render an {en, ur, roman_ur} explanation in the languages the student picked."""
    if not wanted:
        return
    tabs = st.tabs(wanted)
    for tab, label in zip(tabs, wanted):
        with tab:
            text = expl.get(LANGS[label], "") if isinstance(expl, dict) else str(expl)
            if LANGS[label] == "ur":
                st.markdown(f"<div class='urdu'>{text}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='box'>{text}</div>", unsafe_allow_html=True)


def friendly_error(prefix: str, e: Exception):
    msg = str(e)
    if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
        st.error("Rate limit reached on the free Gemini tier. Please wait a minute and try again.")
    elif "API key" in msg or "API_KEY" in msg or "403" in msg or "400" in msg and "key" in msg.lower():
        st.error("The API key looks invalid. Please check your Google AI Studio key.")
    else:
        st.error(f"{prefix} Please try again. ({e})")


# ----------------------------------------------------------------------------
# Session state
# ----------------------------------------------------------------------------
for k, v in {
    "chapter": "",
    "questions": [],
    "quiz": [],
    "quiz_submitted": False,
    "check_result": None,
}.items():
    st.session_state.setdefault(k, v)

# ----------------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------------
with st.sidebar:
    st.title(f"📚 {APP_NAME}")
    st.caption("Matric & Intermediate • English | اردو | Roman Urdu")

    st.text_input("Google AI Studio API key", type="password", key="api_key_input",
                  help="Or set GOOGLE_API_KEY in Streamlit secrets.")
    st.text_input("Model", value=DEFAULT_MODEL, key="model")

    st.divider()
    st.selectbox("Level", ["Matric (9th/10th)", "Intermediate (FSc/FA/ICS)"], key="level")
    st.text_input("Subject (e.g. Biology, Physics, Urdu, Pak Studies)", key="subject")
    wanted_langs = st.multiselect("Explanation languages", list(LANGS), default=list(LANGS))

    st.divider()
    up = st.file_uploader("Upload chapter (PDF, DOCX, TXT)", type=["pdf", "docx", "txt", "md"])
    if up is not None and st.button("📥 Load chapter", use_container_width=True):
        with st.spinner("Reading chapter..."):
            text = extract_text(up).strip()
        if len(text) < 200:
            st.error("Couldn't read enough text. Scanned PDFs need OCR first — try a text-based PDF.")
        else:
            st.session_state.update(chapter=text, questions=[], quiz=[],
                                    quiz_submitted=False, check_result=None)
            st.success(f"Loaded {len(text):,} characters.")
            if len(text) > MAX_CHARS:
                st.warning(f"Chapter is long; only the first {MAX_CHARS:,} characters are used. "
                           "Upload it in smaller parts for full coverage.")

# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
st.title(f"📚 {APP_NAME}")
st.caption("Learn from your own book. Prepare with confidence.")

if not st.session_state["chapter"]:
    st.info("👈 Upload your textbook chapter from the sidebar and click **Load chapter** to begin.")
    st.stop()

tab_q, tab_check, tab_quiz = st.tabs(["📘 Practice Questions", "✍️ Check My Answer", "📝 Quiz"])

# ---------------------------- Practice questions ----------------------------
with tab_q:
    c1, c2, c3 = st.columns(3)
    n_mcq = c1.number_input("MCQs", 0, 20, 5)
    n_short = c2.number_input("Short questions", 0, 15, 5)
    n_long = c3.number_input("Long questions", 0, 8, 2)

    if st.button("✨ Generate practice questions", type="primary"):
        prompt = f"""{chapter_block()}

Create exam practice questions from this chapter:
- {n_mcq} MCQs (type "mcq", 1 mark, with 4 "options" and the correct "answer" text)
- {n_short} short questions (type "short", 2-3 marks)
- {n_long} long questions (type "long", 5-8 marks)

Return a JSON array. Each item:
{{"type": "mcq|short|long", "question": "...", "marks": 1, "options": ["..only for mcq.."],
  "model_answer": "concise ideal answer based only on the chapter"}}"""
        with st.spinner("Creating questions..."):
            try:
                st.session_state["questions"] = ask_llm(base_system(), prompt)
                st.session_state["check_result"] = None
            except Exception as e:
                friendly_error("Could not create questions.", e)

    for i, q in enumerate(st.session_state["questions"], 1):
        st.markdown(f"**Q{i}. [{q.get('type','').upper()} • {q.get('marks','')} mark(s)]** {q['question']}")
        for opt in q.get("options", []) or []:
            st.write(f"- {opt}")
        with st.expander("Show model answer"):
            st.write(q.get("model_answer", ""))

# ------------------------------ Check my answer -----------------------------
with tab_check:
    qs = st.session_state["questions"]
    options = [f"Q{i}. {q['question']}" for i, q in enumerate(qs, 1)] + ["✏️ Type my own question"]
    choice = st.selectbox("Pick a question", options)

    if choice == "✏️ Type my own question":
        question = st.text_area("Your question")
        marks = st.number_input("Marks", 1, 10, 3)
        model_answer = ""
    else:
        idx = options.index(choice)
        question = qs[idx]["question"]
        marks = qs[idx].get("marks", 3)
        model_answer = qs[idx].get("model_answer", "")
        st.caption(f"Marks: {marks}")

    answer = st.text_area("Your answer", height=180, placeholder="Write your answer here...")

    if st.button("✅ Check my answer", type="primary"):
        if not question.strip() or not answer.strip():
            st.warning("Please provide both a question and your answer.")
        else:
            prompt = f"""{chapter_block()}

QUESTION: {question}
MARKS: {marks}
REFERENCE ANSWER (may be empty): {model_answer}
STUDENT ANSWER: {answer}

Check the student's answer against the chapter like an examiner. Return a JSON object:
{{"score": <number out of {marks}>,
  "verdict": "Correct" | "Partially correct" | "Incorrect",
  "strengths": ["..."],
  "missing_or_wrong": ["points missing or wrong, per the chapter"],
  "ideal_answer": "a model answer from the chapter",
  "explanation": {{
     "en": "friendly explanation of mistakes and how to improve, in English",
     "ur": "same explanation in Urdu script",
     "roman_ur": "same explanation in Roman Urdu"}}}}"""
            with st.spinner("Checking..."):
                try:
                    st.session_state["check_result"] = ask_llm(base_system(), prompt)
                    st.session_state["check_marks"] = marks
                except Exception as e:
                    friendly_error("Could not check the answer.", e)

    r = st.session_state["check_result"]
    if r:
        st.subheader(f"Score: {r.get('score')} / {st.session_state.get('check_marks')} — {r.get('verdict')}")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**👍 What you did well**")
            for s in r.get("strengths", []):
                st.write(f"- {s}")
        with col2:
            st.markdown("**⚠️ Missing / wrong**")
            for s in r.get("missing_or_wrong", []):
                st.write(f"- {s}")
        with st.expander("📖 Ideal answer from the chapter"):
            st.write(r.get("ideal_answer", ""))
        st.markdown("### 🗣️ Explanation")
        show_trilingual(r.get("explanation", {}), wanted_langs)

# ---------------------------------- Quiz ------------------------------------
with tab_quiz:
    n_quiz = st.slider("Number of quiz questions", 5, 25, 10)

    if st.button("🎯 Start new quiz", type="primary"):
        prompt = f"""{chapter_block()}

Create {n_quiz} multiple-choice questions from this chapter. Mix easy, medium and hard.
Return a JSON array. Each item:
{{"question": "...", "options": ["A text", "B text", "C text", "D text"],
  "correct_index": 0,
  "explanation": {{"en": "why the answer is correct (English)",
                   "ur": "same in Urdu script",
                   "roman_ur": "same in Roman Urdu"}}}}"""
        with st.spinner("Building quiz..."):
            try:
                st.session_state["quiz"] = ask_llm(base_system(), prompt)
                st.session_state["quiz_submitted"] = False
                for k in [k for k in st.session_state if str(k).startswith("quiz_ans_")]:
                    del st.session_state[k]
            except Exception as e:
                friendly_error("Could not build the quiz.", e)

    quiz = st.session_state["quiz"]
    if quiz:
        for i, q in enumerate(quiz):
            st.markdown(f"**Q{i+1}. {q['question']}**")
            st.radio("Choose one", q["options"], index=None, key=f"quiz_ans_{i}",
                     label_visibility="collapsed", disabled=st.session_state["quiz_submitted"])

        if not st.session_state["quiz_submitted"]:
            if st.button("Submit quiz"):
                st.session_state["quiz_submitted"] = True
                st.rerun()
        else:
            score = sum(
                st.session_state.get(f"quiz_ans_{i}") == q["options"][q["correct_index"]]
                for i, q in enumerate(quiz)
            )
            pct = round(100 * score / len(quiz))
            st.success(f"🏆 Score: {score}/{len(quiz)} ({pct}%)")

            st.markdown("### Review")
            for i, q in enumerate(quiz):
                chosen = st.session_state.get(f"quiz_ans_{i}")
                correct = q["options"][q["correct_index"]]
                with st.expander(f"{'✅' if chosen == correct else '❌'} Q{i+1}. {q['question']}"):
                    st.write(f"Your answer: **{chosen or 'Not answered'}**")
                    st.write(f"Correct answer: **{correct}**")
                    show_trilingual(q.get("explanation", {}), wanted_langs)
