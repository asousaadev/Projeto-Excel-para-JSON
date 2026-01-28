import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL não configurada no arquivo .env")

# Se estiver usando PostgreSQL assíncrono, mude 'postgresql+asyncpg' para 'postgresql' no .env
# Se estiver usando SQLite, a URL deve ser 'sqlite:///./sql_app.db'

# Configuração da Engine Síncrona
engine = create_engine(DATABASE_URL)

# Configuração do Session Local Síncrono
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base Declarativa
Base = declarative_base()

# Dependência do FastAPI (Síncrona)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()