# AI Document Chat - Next Session Prompt

## Project Overview
You're continuing development of a **production-ready RAG (Retrieval-Augmented Generation) service** for legal document chat. This is a FastAPI backend that allows legal professionals to upload PDF documents and ask questions with verifiable citations.

## Current Status - What's Been Built

### ✅ **COMPLETED COMPONENTS**

#### 1. **Smart Chunking System**
- **Location**: `app/utils/chunking.py` (94 lines, clean implementation)
- **Function**: `smart_chunk_document(text: str, chunk_size=900, overlap=150)`
- **Features**: 
  - Cross-page chunks with accurate page tracking
  - Inline page markers `[PAGE:N]` in concatenated text
  - Sentence-aware boundaries
  - Optimal token usage (no artificial page boundaries)

#### 2. **Vector Search System**
- **Location**: `app/utils/vector_search.py` (110 lines)
- **Function**: `search_similar_chunks(query_embedding, top_k=12, document_id)`
- **Features**:
  - Qdrant vector database integration
  - Document-specific filtering
  - Optimized database queries (only essential fields)
  - Returns: `chunk_id`, `similarity_score`, `text`, `page_start`, `page_end`, `token_count`

#### 3. **Rate Limiting System**
- **Location**: `app/utils/rate_limiting.py` (59 lines)
- **Features**: 
  - Redis-based token bucket algorithm
  - Lua script for atomic operations
  - 60 requests per hour per IP (configurable)
  - Human-readable error messages with reset time

#### 4. **Embedding Generation**
- **Location**: `app/utils/embeddings.py` (28 lines)
- **Features**: OpenAI text-embedding-3-small integration

#### 5. **Background Processing**
- **Location**: `app/tasks.py` (103 lines)
- **Features**: 
  - Celery task for document processing
  - Qdrant vector storage
  - PostgreSQL chunk storage
  - Error handling with fallbacks

#### 6. **Infrastructure**
- **Qdrant**: Docker container running on `localhost:6333`
- **PostgreSQL**: Document and chunk storage
- **Redis**: Rate limiting and task queue
- **Celery**: Background processing

## What Needs to Be Built Next

### 🎯 **IMMEDIATE PRIORITY: Ask Endpoint**

#### Current Ask Endpoint Status
- **Location**: `app/routes/ask.py` (26 lines)
- **Current**: Basic skeleton with rate limiting
- **Missing**: LLM integration, vector search, response formatting

#### Required Implementation
```python
@router.post("/ask")
async def ask_question(request: AskRequest, ip_address: str = Depends(get_client_ip)):
    # 1. Rate limiting check (✅ DONE)
    # 2. Generate query embedding
    # 3. Vector search (get top-12 similar chunks)
    # 4. MMR algorithm (select diverse 6 chunks)
    # 5. LLM integration (GPT-4o-mini)
    # 6. Response formatting with citations
```

#### Response Format Required
```json
{
    "answer": "Generated answer with citations",
    "citations": [
        {
            "page": 1,
            "quote": "relevant text snippet",
            "chunk_id": 123
        }
    ],
    "tokens_remaining": 59
}
```

### 🧠 **MMR Algorithm Implementation**
- **Strategy**: Top-12 retrieval → MMR selection → 6 diverse chunks
- **Lambda**: 0.6 (60% relevance, 40% diversity)
- **Purpose**: Prevent redundant information, provide comprehensive context

### 📊 **Data Flow for Ask Endpoint**
```
User Question → Embedding → Vector Search (top-12) → MMR (6 chunks) → 
LLM Context → GPT-4o-mini → Answer + Citations
```

## Technical Architecture

### **Hybrid Database Strategy**
- **PostgreSQL**: Document metadata, chunks with relationships
- **Qdrant**: Vector embeddings for fast similarity search
- **Redis**: Rate limiting, caching, task queue

### **Key Design Decisions Made**
1. **Smart Chunking**: Inline page markers instead of complex character tracking
2. **Qdrant over pgvector**: Due to Windows compilation issues
3. **Rate Limiting**: Redis token bucket with Lua scripts for atomicity
4. **Document Filtering**: Always filter by document_id for security

## File Structure
```
ai-docchat-backend/
├── app/
│   ├── routes/
│   │   ├── ask.py          # 🎯 NEXT: Complete Q&A implementation
│   │   ├── ingest.py       # ✅ PDF upload and processing
│   │   └── ...
│   ├── utils/
│   │   ├── chunking.py     # ✅ Smart chunking
│   │   ├── vector_search.py # ✅ Vector similarity search
│   │   ├── rate_limiting.py # ✅ Redis rate limiting
│   │   ├── embeddings.py   # ✅ OpenAI integration
│   │   └── format_time.py  # ✅ Human-readable time formatting
│   ├── tasks.py            # ✅ Background processing
│   └── models/
│       └── models.py       # ✅ Database models
├── docker-compose.yml      # ✅ Qdrant setup
└── DESIGN.md              # ✅ Updated with current progress
```

## Testing Strategy

### **Current Test Files**
- `test_vector_search.py` - Vector search testing
- `qdrant-setup.py` - Qdrant collection setup
- `explore_qdrant.py` - Qdrant data exploration

### **Testing Commands**
```bash
# Start services
docker-compose up -d qdrant
celery -A app.celery_app worker --pool=eventlet --concurrency=1 --loglevel=info
uvicorn main:app --reload

# Test vector search
python test_vector_search.py
```

## Requirements

### **Functional Requirements**
- ✅ PDF upload and processing
- ✅ Smart chunking with page tracking
- ✅ Vector similarity search
- ✅ Rate limiting
- 🎯 **Q&A with citations** (NEXT)
- 🎯 **MMR for diverse results** (NEXT)

### **Non-Functional Requirements**
- ✅ **Performance**: Sub-second vector search
- ✅ **Scalability**: Redis rate limiting, async processing
- ✅ **Reliability**: Error handling, fallbacks
- 🎯 **Response Time**: <5 seconds for Q&A (NEXT)

## Environment Setup
```bash
# Required services running
- PostgreSQL (localhost:5432)
- Redis (localhost:6379)
- Qdrant (localhost:6333)
- Celery worker
- FastAPI server
```

## Key Implementation Notes

### **Rate Limiting**
- Uses Redis Lua scripts for atomicity
- 60 requests per hour per IP (configurable)
- Human-readable error messages

### **Vector Search**
- Always filters by document_id for security
- Returns optimized data structure
- Handles document-specific queries only

### **Chunking Strategy**
- Concatenated text with `[PAGE:N]` markers
- Cross-page chunks for better context
- Sentence-aware boundaries

## Next Session Goals

1. **Complete ask endpoint** with LLM integration
2. **Implement MMR algorithm** for diverse results
3. **Test end-to-end pipeline** with real questions
4. **Format responses** with proper citations
5. **Add error handling** for edge cases

## Success Criteria
- User can ask questions about uploaded documents
- Responses include accurate citations with page numbers
- Rate limiting prevents abuse
- MMR provides diverse, non-redundant context
- Response time < 5 seconds

---

**Ready to implement the complete Q&A pipeline!** 🚀
