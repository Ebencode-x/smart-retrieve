from app.database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        print("OK: Imeunganishwa na Postgres")
        print(result.fetchone()[0])
except Exception as e:
    print("HITILAFU: Imeshindwa kuunganisha")
    print(e)
