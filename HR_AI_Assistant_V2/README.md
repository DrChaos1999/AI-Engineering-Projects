# HR AI Assistant V2

This project is an HR knowledge assistant built as a web application. It reads HR policy PDFs, indexes them into text chunks, and uses the OpenAI API to answer employee questions with policy-aware responses.

## What changed

- Replaced Google Gemini integration with OpenAI using the official OpenAI Python SDK.
- Switched from a Streamlit frontend to a FastAPI backend serving a modern HTML/JavaScript frontend.
- Added a server-side cache for repeated questions using SQLite.
- Added support for administrator PDF uploads to refresh the knowledge base.

## Architecture

- `app.py`: FastAPI server that serves the web UI and exposes API endpoints for asking questions, listing documents, and uploading PDFs. This backend acts as a simple model control plane, keeping the OpenAI key off the browser.
- `utils/openai_helper.py`: Sends a policy-aware prompt to OpenAI and returns the generated answer.
- `utils/pdf_reader.py`: Reads all PDFs from `data/`, extracts text, and splits it into chunks.
- `database/database.py`: Caches question/answer pairs locally in SQLite.
- `static/index.html`: New HTML/JavaScript frontend with login, chat, and admin upload functionality.
- `assets/style.css`: Shared styling for the frontend.

## Setup

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

2. Copy the example environment file and add your OpenAI key:

```bash
copy .env.example .env
```

3. Fill in `.env`:

```text
OPENAI_API_KEY=your_openai_api_key_here
```

4. Start the server:

```bash
python app.py
```

5. Open `http://localhost:8000` in your browser.

## Credentials

- Admin: `admin` / `parvezai`
- Employee: `employee` / `trimco123`

## Notes

- Uploaded PDFs are stored in the `data/` directory.
- Answers are cached in `database/hr_ai.db` to reduce OpenAI usage.
- This is a prototype application for internal HR policy search and question answering.
