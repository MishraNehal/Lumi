# 🔮 Lumi — AI Personal Knowledge Assistant

Lumi is a retrieval-augmented AI assistant that lets you build a personal knowledge base from your own documents, websites, and YouTube videos — then chat with it using source-cited, hallucination-checked answers.

Upload a PDF, paste a YouTube lecture link, or add a webpage — Lumi ingests it once, remembers it, and answers questions about it in later sessions, with citations back to the exact page, timestamp, or URL.

---

## ✨ Features

- **Multi-format ingestion** — PDF, DOCX, PPTX, XLSX, TXT, code files, images (OCR), scanned PDFs (OCR), web pages, and YouTube videos with transcript timestamps
- **Per-user knowledge bases** — every user's uploaded content is isolated in its own vector store
- **Hybrid retrieval** — combines dense vector search (Chroma) with sparse keyword search (BM25) using Reciprocal Rank Fusion, then reranks results with a cross-encoder
- **LangGraph-powered RAG pipeline** — explicit graph of nodes for:
  - Intent classification
  - Query rewriting for follow-up questions
  - Retrieval retry/self-correction
  - Context-grounded answer generation
  - Faithfulness verification
- **Source-aware citations** — PDF page numbers, YouTube timestamps, and web URLs
- **Ask this source** — restrict a question to one specific document, page, or video
- **Persistent chat history** — resume, rename, search, archive, favorite, or delete conversations
- **Streaming responses** — token-by-token responses with live status updates (`Searching → Generating → Verifying`)
- **JWT authentication** — signup/login with user-scoped data
- **Conversational memory** — remembers details within a chat session

---

## 🏗️ Architecture

```text
Streamlit UI
     │
     ▼
FastAPI Backend ───────────────► SQLite
     │                            │
     │                            ├── Users
     │                            ├── Conversations
     │                            ├── Messages
     │                            └── Query Logs
     │
     ▼
LangGraph RAG Pipeline
     │
     ├── Intent Classification
     │       ├── Conversational ──► Direct Reply
     │       └── Document Question
     │                    │
     │                    ▼
     │             Check Knowledge Base
     │                    │
     │                    ▼
     │             Rewrite Query
     │                    │
     │                    ▼
     │        Hybrid Retrieval
     │        ┌───────────┴───────────┐
     │        ▼                       ▼
     │   Chroma Vector             BM25 Search
     │        │                       │
     │        └───────────┬───────────┘
     │                    ▼
     │          Reciprocal Rank Fusion
     │                    │
     │                    ▼
     │             Cross-Encoder Reranker
     │                    │
     │                    ▼
     │              Build Context
     │                    │
     │                    ▼
     │             Generate Answer
     │                    │
     │                    ▼
     │          Faithfulness Verification
     │                    │
     │                    ▼
     │             Stream to UI
     │
     └── Retry / Broaden Search
              ▲
              │
        If retrieval fails
```

### Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | FastAPI |
| RAG Orchestration | LangChain + LangGraph |
| Vector Database | ChromaDB |
| Sparse Retrieval | BM25 |
| Embeddings | sentence-transformers |
| Reranking | Cross-Encoder |
| LLM | Groq |
| Database | SQLite |
| Authentication | JWT |
| OCR | Tesseract + Poppler |

---

## 📁 Project Structure

```text
Lumi/
├── backend/
│   ├── main.py                  # FastAPI application entrypoint
│   ├── auth/                    # JWT authentication and security
│   ├── database/                # SQLite models and Chroma configuration
│   ├── ai/                      # LangGraph pipeline, prompts, LLM and reranker
│   ├── routers/                 # API endpoints
│   ├── services/                # Document, web, YouTube and OCR ingestion
│   └── utils/                   # Transcript and OCR utilities
│
├── frontend/
│   └── app.py                   # Streamlit application
│
└── README.md
```

---

## ⚙️ Setup

### 1. Clone the repository

```bash
git clone https://github.com/MishraNehal/Lumi.git
cd Lumi
```

### 2. Create a virtual environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS / Linux

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

---

## 🔐 Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
SECRET_KEY=your_random_secret_key_here
```

Generate a strong secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Optional OCR Configuration

If Tesseract or Poppler is installed in a custom location:

```env
TESSERACT_CMD=C:\path\to\tesseract.exe
POPPLER_PATH=C:\path\to\poppler\Library\bin
```

---

## 🖼️ OCR Setup

OCR is required only for image uploads and scanned PDFs.

### Tesseract-OCR

1. Download and install Tesseract-OCR.
2. Use the default installation path if possible.
3. If required, configure `TESSERACT_CMD` in `.env`.

### Poppler

Poppler is required for scanned PDF processing.

1. Download a Windows build of Poppler.
2. Extract it.
3. Add the `Library\bin` path to `POPPLER_PATH`.

---

## ▶️ Run Lumi

Open two terminals.

### Terminal 1 — Backend

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

### Terminal 2 — Frontend

```bash
streamlit run frontend/app.py
```

### Optional HTML frontend

The project also includes a standalone HTML/CSS/JavaScript frontend in `web/`. Keep the
FastAPI backend running, then open a third terminal:

```bash
cd web
python -m http.server 5500
```

Open `http://localhost:5500` in your browser. The Streamlit frontend remains available
at the URL shown by `streamlit run frontend/app.py`.

Then open the Streamlit URL shown in the terminal, usually:

```text
http://localhost:8501
```

FastAPI interactive documentation is available at:

```text
http://127.0.0.1:8000/docs
```

> **Windows note:** Avoid `--reload` during active ingestion because file writes can trigger server restarts and interrupt in-flight requests.

---

## 🔌 API Overview

| Endpoint | Method | Description |
|---|---|---|
| `/auth/signup` | POST | Create a user account |
| `/auth/login` | POST | Authenticate a user |
| `/ingest/document` | POST | Upload PDF/DOCX/PPTX/XLSX/TXT/image files |
| `/ingest/web` | POST | Ingest a webpage by URL |
| `/ingest/youtube` | POST | Ingest a YouTube transcript |
| `/ingest/ocr` | POST | OCR an image or scanned document |
| `/sources` | GET / DELETE | List or delete sources |
| `/chat` | POST | Ask a question |
| `/chat/stream` | POST | Ask a question with streaming |
| `/conversations` | GET | List conversations |
| `/conversations/{id}` | PATCH / DELETE | Update or delete a conversation |
| `/conversations/{id}/messages` | GET | Retrieve message history |

---

## 🧠 RAG Workflow

Lumi follows a multi-stage retrieval pipeline:

```text
User Question
      │
      ▼
Intent Classification
      │
      ▼
Query Rewriting
      │
      ▼
┌─────────────────────────────┐
│       Hybrid Retrieval      │
│                             │
│  Chroma Vector + BM25       │
│            ↓                │
│   Reciprocal Rank Fusion    │
│            ↓                │
│     Cross-Encoder Reranker  │
└─────────────────────────────┘
      │
      ▼
Relevant Context
      │
      ▼
LLM Answer Generation
      │
      ▼
Faithfulness Verification
      │
      ▼
Cited Answer
```

This design helps Lumi handle both semantic questions and exact keyword-based queries while reducing unsupported answers.

---

## 📚 Supported Sources

Lumi can build a knowledge base from:

- PDF documents
- DOCX files
- PPTX presentations
- XLSX spreadsheets
- TXT files
- Source-code files
- Images
- Scanned PDFs
- Web pages
- YouTube videos and lectures

---

## 🗺️ Roadmap

- [ ] Multi-source comparison
- [ ] Automated test suite
- [ ] Study Mode with quizzes and flashcards
- [ ] Docker deployment guide
- [ ] Production deployment
- [ ] Advanced source analytics

---

## 👤 Author

**Nehal Mishra**

B.Tech CSE (AI & ML)
Acropolis Institute of Technology & Research (AITR), Indore

- GitHub: https://github.com/MishraNehal
- LinkedIn: https://linkedin.com/in/nehal-mishra-263a97324/

---

## ⭐ Project Highlights

Lumi demonstrates practical implementation of:

- Retrieval-Augmented Generation (RAG)
- Agentic / graph-based AI workflows
- Hybrid information retrieval
- Semantic search
- Cross-encoder reranking
- OCR-based document understanding
- Conversational AI
- Source-grounded generation
- JWT-based authentication
- Streaming AI responses
- Multi-user knowledge isolation

---

## 📄 License

Add your preferred open-source license here, such as MIT, before publishing the repository.
