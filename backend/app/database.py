# app/database.py
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL não configurada no arquivo .env")

# Configuração da Engine Assíncrona
engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# Configuração do Session Local Assíncrono
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base Declarativa
Base = declarative_base()

# Dependência do FastAPI para obter a sessão do banco de dados
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
