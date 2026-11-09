# 📚 Exam Mentor

A Streamlit app that helps **Matric** and **Intermediate** students prepare for exams using their **own textbook chapters**. Explanations are available in **English, اردو (Urdu) and Roman Urdu**.

Powered by the **Google AI Studio (Gemini) API**.

## Features

- **Upload a chapter** (PDF, DOCX or TXT)
- **Practice Questions**: auto-generated MCQs, short and long questions with hidden model answers
- **Check My Answer**: get a score, strengths, missing points, the ideal answer, and an explanation in English, Urdu and Roman Urdu
- **Quiz mode**: MCQ quiz with a score and a per-question review in three languages

## Project structure

```
.
├── app.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Step 1: Get a Google AI Studio API key

1. Open [aistudio.google.com](https://aistudio.google.com) and sign in with a Google account.
2. Click **Get API key** → **Create API key**.
3. Copy the key. Keep it private.

## Step 2: Run locally

```bash
git clone <your-repo-url>
cd <your-repo-folder>
pip install -r requirements.txt
```

Create `.streamlit/secrets.toml`:

```toml
GOOGLE_API_KEY = "your-key-here"
```

(Or skip this and paste the key into the sidebar when the app opens.)

Start the app:

```bash
streamlit run app.py
```

## Step 3: Push to GitHub

```bash
git init
git add app.py requirements.txt README.md .gitignore
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

The `.gitignore` keeps your `secrets.toml` out of GitHub. Never upload your API key.

## Step 4: Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and click **New app**.
2. Select your GitHub repo, the `main` branch, and `app.py`.
3. Open **Advanced settings → Secrets** and add:

   ```toml
   GOOGLE_API_KEY = "your-key-here"
   ```

4. Click **Deploy**.

## Configuration

| Setting | Where | Notes |
|---|---|---|
| `GOOGLE_API_KEY` | Streamlit secrets or sidebar | Required |
| Model | Sidebar field | Default `gemini-2.5-flash`, editable |
| `APP_NAME` | Top of `app.py` | Change to rename the app |
| `MAX_CHARS` | Top of `app.py` | Chapter characters sent to the model (default 60,000) |

## Limitations

- Only **text-based PDFs** are supported. Scanned books need OCR first.
- Very long chapters are truncated to `MAX_CHARS`. Upload them in parts.
- The free Gemini tier has rate limits. If you see a limit message, wait a minute and retry.
- AI-generated questions and marking can contain mistakes. Verify important answers with the textbook and a teacher.

## Tech stack

- [Streamlit](https://streamlit.io)
- [Google Gemini API](https://ai.google.dev) via the `google-genai` SDK
- `pypdf` and `python-docx`

## License

Add your preferred license (for example MIT) here.
