from app.database import engine, Base
from app.models.violation import Violation

Base.metadata.create_all(bind=engine)

print("Tables created")