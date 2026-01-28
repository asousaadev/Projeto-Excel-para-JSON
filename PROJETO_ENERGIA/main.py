import os
from datetime import date, datetime
from typing import List, Optional
from decimal import Decimal

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from sqlalchemy import (
    create_engine, Column, Integer, String, Boolean, 
    ForeignKey, Numeric, TIMESTAMP, Date
)
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import func

# --- Configuração de Ambiente e Banco de Dados ---
# Usa variável de ambiente ou valor padrão para dev
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/energia_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Modelos SQLAlchemy (Baseado em bancoPostegre.docx) ---

class Cliente(Base):
    __tablename__ = "clientes"

    id_cliente = Column(Integer, primary_key=True, index=True)
    cnpj = Column(String(18), unique=True, nullable=False, index=True)
    nome_empresa = Column(String(255), nullable=False, index=True)
    nome_da_unidade = Column(String(255))
    url_logo = Column(String(2048))
    endereco = Column(String(500))
    cidade = Column(String(100))
    estado = Column(String(2))
    subgrupo = Column(String(50))
    classe = Column(String(50))
    modalidade_contrato = Column(String(100))
    id_unico_concessionaria = Column(String(50))
    has_geracao_distribuida = Column(Boolean, default=False)
    data_criacao = Column(TIMESTAMP(timezone=True), server_default=func.now())
    data_atualizacao = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    faturas = relationship("Fatura", back_populates="cliente", cascade="all, delete-orphan")

class Fatura(Base):
    __tablename__ = "faturas"

    id_fatura = Column(Integer, primary_key=True, index=True)
    id_cliente = Column(Integer, ForeignKey("clientes.id_cliente", ondelete="CASCADE"), nullable=False)
    data_faturamento = Column(TIMESTAMP, nullable=False) # Mês/Ano referência

    # Dados de Demanda
    demanda_contratada_ponta_kw = Column(Numeric(10, 2))
    demanda_contratada_f_ponta_kw = Column(Numeric(10, 2))
    demanda_ponta_kw = Column(Numeric(10, 2), default=0.00)
    demanda_f_ponta_kw = Column(Numeric(10, 2), default=0.00)
    demanda_maxima_registrada_kw = Column(Numeric(10, 2), default=0.00)

    # Dados de Consumo
    consumo_ponta_kwh = Column(Numeric(12, 2), default=0.00)
    consumo_ponta_vl = Column(Numeric(12, 2), default=0.00)
    consumo_fora_ponta_kwh = Column(Numeric(12, 2), default=0.00)
    consumo_fora_ponta_vl = Column(Numeric(12, 2), default=0.00)
    consumo_total_kwh = Column(Numeric(12, 2), default=0.00) # Coluna auxiliar/calculada

    # Valores Totais e Perdas (Simplificado para o exemplo)
    valor_total_fatura = Column(Numeric(12, 2), nullable=False, default=0.00)
    valor_perdas_total = Column(Numeric(12, 2), default=0.00) # Ex: Reativo + Ultrapassagem

    cliente = relationship("Cliente", back_populates="faturas")

# Criação das tabelas (em produção usar Alembic para migrações)
Base.metadata.create_all(bind=engine)

# --- Schemas Pydantic ---

class FaturaBase(BaseModel):
    data_faturamento: datetime
    demanda_contratada_ponta_kw: Optional[float] = 0.0
    demanda_contratada_f_ponta_kw: Optional[float] = 0.0
    valor_total_fatura: float
    valor_perdas_total: Optional[float] = 0.0
    consumo_ponta_kwh: Optional[float] = 0.0
    consumo_fora_ponta_kwh: Optional[float] = 0.0

class FaturaCreate(FaturaBase):
    pass

class FaturaResponse(FaturaBase):
    id_fatura: int
    id_cliente: int
    
    class Config:
        orm_mode = True

class ClienteBase(BaseModel):
    cnpj: str
    nome_empresa: str
    nome_da_unidade: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    
    @validator('cnpj')
    def validate_cnpj(cls, v):
        if len(v) < 14: # Validação simples
            raise ValueError('CNPJ inválido')
        return v

class ClienteCreate(ClienteBase):
    pass

class ClienteResponse(ClienteBase):
    id_cliente: int
    faturas: List[FaturaResponse] = []

    class Config:
        orm_mode = True

# --- Schemas do Dashboard ---
class DashboardCards(BaseModel):
    custo_mensal: float
    perda_mensal: float

class GraficoData(BaseModel):
    labels: List[str]
    values: List[float]

class DashboardResponse(BaseModel):
    cards: DashboardCards
    grafico_custo_loja: GraficoData
    grafico_top_perdas: GraficoData

# --- Dependências ---

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Aplicação FastAPI ---

app = FastAPI(title="API Projeto Energia", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Tratamento de Erros ---

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"message": "Erro interno no banco de dados.", "detail": str(exc)},
    )

# --- Endpoints CRUD Clientes ---

@app.post("/clientes/", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED)
def create_cliente(cliente: ClienteCreate, db: Session = Depends(get_db)):
    db_cliente = db.query(Cliente).filter(Cliente.cnpj == cliente.cnpj).first()
    if db_cliente:
        raise HTTPException(status_code=400, detail="CNPJ já cadastrado")
    
    new_cliente = Cliente(**cliente.dict())
    db.add(new_cliente)
    db.commit()
    db.refresh(new_cliente)
    return new_cliente

@app.get("/clientes/", response_model=List[ClienteResponse])
def read_clientes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    clientes = db.query(Cliente).offset(skip).limit(limit).all()
    return clientes

@app.get("/clientes/{cliente_id}", response_model=ClienteResponse)
def read_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id_cliente == cliente_id).first()
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return cliente

@app.put("/clientes/{cliente_id}", response_model=ClienteResponse)
def update_cliente(cliente_id: int, cliente: ClienteCreate, db: Session = Depends(get_db)):
    db_cliente = db.query(Cliente).filter(Cliente.id_cliente == cliente_id).first()
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    for key, value in cliente.dict().items():
        setattr(db_cliente, key, value)
    
    db.commit()
    db.refresh(db_cliente)
    return db_cliente

@app.delete("/clientes/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cliente(cliente_id: int, db: Session = Depends(get_db)):
    db_cliente = db.query(Cliente).filter(Cliente.id_cliente == cliente_id).first()
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    db.delete(db_cliente)
    db.commit()
    return None

# --- Endpoints CRUD Faturas ---

@app.post("/clientes/{cliente_id}/faturas/", response_model=FaturaResponse)
def create_fatura_for_cliente(cliente_id: int, fatura: FaturaCreate, db: Session = Depends(get_db)):
    # Verifica se o cliente existe
    db_cliente = db.query(Cliente).filter(Cliente.id_cliente == cliente_id).first()
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    new_fatura = Fatura(**fatura.dict(), id_cliente=cliente_id)
    db.add(new_fatura)
    db.commit()
    db.refresh(new_fatura)
    return new_fatura

# --- Endpoint Dashboard (Para main.js) ---

@app.get("/api/dashboard/resumo", response_model=DashboardResponse)
def get_dashboard_data(db: Session = Depends(get_db)):
    """
    Retorna dados agregados para o dashboard. 
    Lógica: Soma os custos e perdas do mês atual (simulado aqui pegando todas as faturas para exemplo).
    """
    
    # 1. Totais (Cards)
    total_custo = db.query(func.sum(Fatura.valor_total_fatura)).scalar() or 0.0
    total_perda = db.query(func.sum(Fatura.valor_perdas_total)).scalar() or 0.0

    # 2. Gráfico Custo por Loja (Agrupado por Cliente)
    custos_por_loja = db.query(
        Cliente.nome_da_unidade, 
        func.sum(Fatura.valor_total_fatura)
    ).join(Fatura).group_by(Cliente.id_cliente).all()

    labels_custo = [c[0] for c in custos_por_loja if c[0]]
    values_custo = [float(c[1]) for c in custos_por_loja if c[1] is not None]

    # 3. Gráfico Top Perdas (Agrupado por Cliente, ordenado desc)
    perdas_por_loja = db.query(
        Cliente.nome_da_unidade, 
        func.sum(Fatura.valor_perdas_total)
    ).join(Fatura).group_by(Cliente.id_cliente).order_by(func.sum(Fatura.valor_perdas_total).desc()).limit(10).all()

    labels_perdas = [p[0] for p in perdas_por_loja if p[0]]
    values_perdas = [float(p[1]) for p in perdas_por_loja if p[1] is not None]

    return {
        "cards": {
            "custo_mensal": float(total_custo),
            "perda_mensal": float(total_perda)
        },
        "grafico_custo_loja": {
            "labels": labels_custo,
            "values": values_custo
        },
        "grafico_top_perdas": {
            "labels": labels_perdas,
            "values": values_perdas
        }
    }