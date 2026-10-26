from app.database import engine, Base
from app import db_models


Base.metadata.create_all(bind=engine)

print("Tables created.")