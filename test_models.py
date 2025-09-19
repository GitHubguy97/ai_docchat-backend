from app.database import engine
from app.models.models import Document, Chunk, Embedding, Base

def test_models():
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created successfully!")
        
        # Test creating a document
        from app.database import SessionLocal
        db = SessionLocal()
        
        # Create a test document
        test_doc = Document(
            content_hash="test_hash_123",
            title="Test Document",
            pages=5,
            bytes=10000,
            status="ready"
        )
        
        db.add(test_doc)
        db.commit()
        print(f"✅ Document created with ID: {test_doc.id}")
        
        # Test querying
        found_doc = db.query(Document).filter(Document.content_hash == "test_hash_123").first()
        print(f"✅ Found document: {found_doc.title}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_models()