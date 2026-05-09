from backend.database.db import engine, Base
from backend.database.models import Transaction, Prediction

Base.metadata.create_all(bind=engine)

print("Database and tables created successfully!")