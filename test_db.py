from app.database import engine, SessionLocal
from sqlalchemy import text

def test_connection():
  try:
    with engine.connect() as connection:
      result = connection.execute(text("SELECT 1"))
      print("Database connection successful")
      print(f"Result: {result.fetchone()}")

    db = SessionLocal()
    print("Session creation successful!")
    db.close()
  except Exception as e:
    print(f"Database connection failed: {e}")


if __name__ == "__main__":
  test_connection()