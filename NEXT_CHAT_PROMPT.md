# AI Document Chat - Next Chat Context

## Project Overview

You are working on a **production-ready RAG (Retrieval-Augmented Generation) service** for single-document chat, specifically designed for legal document analysis. This is a complete full-stack application with a FastAPI backend and React frontend.

## What We're Building

**Primary Goal:** Legal professionals can upload contracts, agreements, or legal documents and ask questions about them with verifiable citations and legal rule scanning.

**Key Features:**
- PDF upload and processing with smart chunking
- AI-powered question answering with exact citations
- Click-to-page navigation for precise document references
- Real-time processing status updates
- Rate limiting and caching for production use

## Current Status: 95% Complete

### ✅ What's Working
1. **Complete Backend System**
   - FastAPI with all endpoints (`/ingest`, `/ask`, `/jobs`, `/health`)
   - Smart chunking with cross-page support and accurate page tracking
   - OpenAI integration for embeddings and LLM responses
   - Qdrant vector database for similarity search
   - Redis for caching, rate limiting, and job status
   - Enhanced search with structured question decomposition
   - Answer caching for consistent responses

2. **Complete Frontend System**
   - React 18 with Vite, Tailwind CSS, react-pdf
   - PDF viewer with text extraction and highlighting capabilities
   - Chat interface with real-time status updates
   - Smart progress bar with status-based jumps
   - Custom hooks for state management
   - API integration with error handling

3. **Production Features**
   - Rate limiting (60 requests/hour per IP)
   - Idempotency (same document hash = same result)
   - Error handling throughout the stack
   - CORS configuration for frontend communication
   - Job status tracking with real-time updates

### 🔄 What's Left (Only 1 Major Task)
- **Citation Highlighting**: Implement frontend click-to-page functionality for exact text search

## Technical Architecture

### Backend (FastAPI + Celery + PostgreSQL + Qdrant + Redis)
```
ai-docchat-backend/
├── main.py                 # FastAPI app with CORS
├── app/
│   ├── models/models.py    # SQLAlchemy models
│   ├── routes/             # API endpoints
│   │   ├── ingest.py       # PDF upload
│   │   ├── ask.py          # Q&A with caching
│   │   ├── jobs.py         # Job status
│   │   └── health.py       # Health checks
│   ├── utils/              # Core utilities
│   │   ├── chunking.py     # Smart chunking
│   │   ├── enhanced_search.py # Question decomposition
│   │   ├── answer_generation.py # LLM + caching
│   │   ├── vector_search.py # Qdrant search
│   │   └── rate_limiting.py # Redis token bucket
│   ├── tasks.py            # Celery background processing
│   └── config.py           # Settings
```

### Frontend (React + Vite + Tailwind)
```
ai-docchat/
├── src/
│   ├── components/
│   │   ├── App.jsx         # Main app
│   │   ├── PdfPane.jsx     # PDF viewer
│   │   ├── ChatPane.jsx    # Chat interface
│   │   └── ProgressBar.jsx # Progress indicator
│   ├── hooks/
│   │   ├── useDocumentProcessing.js # Document state
│   │   └── useChat.js      # Chat state
│   └── services/api.js     # Backend integration
```

## Key Technical Implementations

### 1. Smart Chunking
- Uses inline page markers `[PAGE:N]` in concatenated text
- Creates cross-page chunks for related content
- Prefers sentence boundaries for clean breaks
- Accurate page tracking for each chunk

### 2. Enhanced Search
- OpenAI function calling breaks complex questions into sub-questions
- Multi-query search (each sub-question searched separately)
- Deduplication while preserving relevance order
- Fallback to simple search if parsing fails

### 3. LLM Integration
- GPT-4o-mini for answer generation
- Structured citation format with exact quotes
- Redis-based answer caching for consistency
- Question normalization for cache keys

### 4. Vector Search
- Qdrant for fast similarity search
- PostgreSQL for chunk metadata
- Document filtering for security
- Optimized field retrieval

## Current Data Flow

### Document Processing
```
PDF Upload → Validation → Content Hashing → Idempotency Check → 
Database Storage → Celery Task → PDF Parsing → Smart Chunking → 
Embedding Generation → Qdrant Vector Storage → Ready for Q&A
```

### Question Answering
```
Question → Enhanced Search → Vector Retrieval → LLM Generation → 
Answer with Citations → Frontend Display → Click-to-Page Navigation
```

## Environment Setup

### Backend Dependencies
- Python 3.12+ with virtual environment
- PostgreSQL 16+ (local or Docker)
- Redis (local)
- Qdrant (Docker: `docker run -p 6333:6333 qdrant/qdrant`)
- OpenAI API key

### Frontend Dependencies
- Node.js 18+
- React 18, Vite, Tailwind CSS
- react-pdf for PDF viewing

### Running the System
1. **Backend**: `cd ai-docchat-backend && uvicorn main:app --reload`
2. **Celery**: `cd ai-docchat-backend && celery -A app.celery_app worker --pool=eventlet --concurrency=1`
3. **Frontend**: `cd ai-docchat && npm run dev`
4. **Qdrant**: `docker run -p 6333:6333 qdrant/qdrant`

## What You Need to Do Next

### Primary Task: Citation Highlighting
The only major remaining feature is implementing frontend click-to-page functionality:

1. **Citation Click Handler**: When user clicks a citation, jump to the correct page
2. **Exact Text Search**: Search for the exact quote text on the specified pages
3. **Text Highlighting**: Highlight the found text in the PDF viewer
4. **Multi-page Support**: Handle citations that span multiple pages

### Technical Details for Citation Highlighting
- Citations come from backend with `exact_text` and `search_pages` fields
- `search_pages` is an array of page numbers to search
- `exact_text` is the exact quote to find and highlight
- Use `react-pdf`'s text layer for highlighting
- Implement search within PDF text content

### Files to Focus On
- `ai-docchat/src/components/PdfPane.jsx` - PDF viewer and highlighting
- `ai-docchat/src/components/ChatPane.jsx` - Citation click handlers
- `ai-docchat/src/App.jsx` - Communication between components

## Testing the System

### Backend Testing
- Upload a PDF via `/ingest` endpoint
- Check job status via `/jobs/{id}` endpoint
- Ask questions via `/ask` endpoint
- Verify caching works with repeated questions

### Frontend Testing
- Upload a PDF through the UI
- Watch the progress bar update
- Ask questions and see answers with citations
- Test error handling (network issues, rate limiting)

## Important Notes

1. **No Logging**: We removed all logging code to get back to a working state
2. **CORS**: Backend allows `localhost:5173`, `localhost:3000`, and `localhost:8000`
3. **Rate Limiting**: 60 requests per hour per IP address
4. **Caching**: Answers are cached for 1 hour by default
5. **Error Handling**: Comprehensive error handling throughout

## Success Criteria

The system is considered complete when:
- [ ] Citations are clickable and jump to the correct page
- [ ] Exact text is highlighted in the PDF viewer
- [ ] Multi-page citations work correctly
- [ ] End-to-end testing passes with real documents

## Questions to Ask

If you need clarification on anything:
1. How does the current citation system work?
2. What's the structure of citation data from the backend?
3. How should multi-page citations be handled?
4. What's the best approach for text highlighting in react-pdf?

---

**This is a production-ready system that just needs the final citation highlighting feature to be complete.**

