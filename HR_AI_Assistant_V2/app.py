import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from database.database import create_database, get_cached_answer, save_answer
from utils.openai_helper import ask_openai
from utils.pdf_reader import read_all_pdfs

env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path)

if not os.getenv('OPENAI_API_KEY') and env_path.exists():
    # Some editors save .env files with a BOM. Load it manually if needed.
    env_text = env_path.read_text(encoding='utf-8-sig')
    for line in env_text.splitlines():
        if not line or line.strip().startswith('#'):
            continue
        if '=' not in line:
            continue
        key, _, value = line.partition('=')
        if key.strip() == 'OPENAI_API_KEY':
            os.environ.setdefault('OPENAI_API_KEY', value.strip())

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise RuntimeError('OPENAI_API_KEY is not set in the environment.')

DATA_FOLDER = Path('data')
DATA_FOLDER.mkdir(parents=True, exist_ok=True)

app = FastAPI(title='HR AI Assistant', version='2.0')
app.mount('/assets', StaticFiles(directory='assets'), name='assets')


class AskRequest(BaseModel):
    question: str


@app.on_event('startup')
def startup_event():
    create_database()
    read_all_pdfs.cache_clear()
    read_all_pdfs(str(DATA_FOLDER))


@app.get('/', response_class=HTMLResponse)
def read_index():
    index_file = Path('static/index.html')
    return HTMLResponse(index_file.read_text(encoding='utf-8'))


@app.get('/api/docs')
def list_documents():
    pdf_files = [f for f in os.listdir(DATA_FOLDER) if f.lower().endswith('.pdf')]
    return {'documents': sorted(pdf_files)}


@app.post('/api/ask')
def ask_question(request: AskRequest):
    question_text = request.question.strip()
    if not question_text:
        raise HTTPException(status_code=400, detail='Question must not be empty.')

    cached_answer = get_cached_answer(question_text)
    if cached_answer:
        return {'answer': cached_answer, 'cached': True}

    chunks = read_all_pdfs(str(DATA_FOLDER))
    context = get_relevant_chunks(chunks, question_text)
    answer = ask_openai(OPENAI_API_KEY, context, question_text)

    save_answer(question_text, answer)
    return {'answer': answer, 'cached': False}


@app.post('/api/upload')
def upload_document(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail='Only PDF files are supported.')

    output_path = DATA_FOLDER / file.filename
    with output_path.open('wb') as buffer:
        buffer.write(file.file.read())

    read_all_pdfs.cache_clear()
    read_all_pdfs(str(DATA_FOLDER))

    return {'message': f'{file.filename} uploaded successfully.'}


def get_relevant_chunks(chunks, question, max_chunks=3):
    question_words = set(question.lower().split())
    scored = []
    for chunk in chunks:
        chunk_lower = chunk.lower()
        score = 0
        for word in question_words:
            if word in chunk_lower:
                score += 1
        score += len(chunk) / 1000
        scored.append((score, chunk))
    scored.sort(reverse=True, key=lambda x: x[0])
    top_chunks = [c[1] for c in scored[:max_chunks]]
    return '\n'.join(top_chunks)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app:app', host='0.0.0.0', port=8000, reload=True)
