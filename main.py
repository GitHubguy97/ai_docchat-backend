from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import health, ask, ingest, documents, jobs

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8000"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
  return {"message": "Hello World"}

app.include_router(health.router)
app.include_router(ask.router)
app.include_router(ingest.router)
app.include_router(documents.router)
app.include_router(jobs.router)
