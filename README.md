# 🌟 Lumi — AI Personal Knowledge Assistant

Lumi is a modular, open-source **AI Personal Knowledge Assistant** built using **FastAPI**, **LangChain**, and **Hugging Face models**.  
It enables users to ingest knowledge from multiple sources and ask grounded, context-aware questions through a unified chat interface.

Lumi follows **industry-style backend architecture** with clear separation of concerns, making it ideal for **hands-on learning, experimentation, and interview-ready demonstrations**.

---

## 🚀 Features

- 📄 **Document Ingestion**
  - Supports PDF, TXT, DOCX, PPTX, XLS/XLSX, and code files
- 🖼 **OCR Support**
  - Extracts text from images and scanned PDFs using Tesseract OCR
- 🎥 **YouTube Knowledge Ingestion**
  - Fetches video transcripts (auto/manual captions) using open-source tools
- 🌐 **Web Page Ingestion**
  - Scrapes and cleans webpage content for knowledge extraction
- 🧠 **RAG-Based Question Answering**
  - Uses Retrieval-Augmented Generation to answer questions strictly from ingested data
- 📚 **Source Citations**
  - Every response includes its data sources (document / OCR / YouTube / web)
- 🚫 **Hallucination Control**
  - Responds with *"I don't know based on the provided data"* when information is missing

---


