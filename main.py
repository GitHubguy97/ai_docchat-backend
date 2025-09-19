from fastapi import FastAPI
from app.routes import health, ask, ingest, documents

app = FastAPI()

@app.get("/")
def root():
  return {"message": "Hello World"}

app.include_router(health.router)
app.include_router(ask.router)
app.include_router(ingest.router)
app.include_router(documents.router)
