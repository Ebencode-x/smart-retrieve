from app.database import engine
from app.models import Base

Base.metadata.create_all(bind=engine)
print("OK: Majedwali yameundwa (users, id_card_reports, clearance_passes)")
