# main.py
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db, engine, Base
from app.models import Cliente, Fatura

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
        if len(v) < 14:
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

# --- Aplicação FastAPI ---

app = FastAPI(title="API Projeto Energia", version="1.0.0")

# --- Eventos de Startup Assíncronos ---
@app.on_event("startup")
async def startup_event():
    # Cria as tabelas assíncronamente ao iniciar a aplicação
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

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
    db_cliente = db.query(Cliente).filter(Cliente.id_cliente == cliente_id).first()
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    new_fatura = Fatura(**fatura.dict(), id_cliente=cliente_id)
    db.add(new_fatura)
    db.commit()
    db.refresh(new_fatura)
    return new_fatura

# --- Endpoint Dashboard (Finalizado) ---

@app.get("/api/dashboard/resumo", response_model=DashboardResponse)
def get_dashboard_resumo(db: Session = Depends(get_db)):
    """
    Calcula e retorna os dados agregados para o dashboard principal.
    """
    
    cards_data = db.query(
        func.sum(Fatura.valor_total_fatura).label("custo_mensal"),
        func.sum(Fatura.valor_perdas_total).label("perda_mensal")
    ).first()

    cards_response = DashboardCards(
        custo_mensal=float(cards_data.custo_mensal or 0.0),
        perda_mensal=float(cards_data.perda_mensal or 0.0)
    )

    grafico_custo_data = db.query(
        Cliente.nome_empresa,
        func.sum(Fatura.consumo_total_kwh).label("total_kwh")
    ).join(Fatura).group_by(Cliente.nome_empresa).order_by(func.sum(Fatura.consumo_total_kwh).desc()).all()

    grafico_custo_response = GraficoData(
        labels=[row.nome_empresa for row in grafico_custo_data],
        values=[float(row.total_kwh or 0.0) for row in grafico_custo_data]
    )
    
    grafico_perdas_data = db.query(
        Cliente.cidade,
        func.sum(Fatura.valor_perdas_total).label("total_perdas")
    ).join(Fatura).group_by(Cliente.cidade).order_by(func.sum(Fatura.valor_perdas_total).desc()).limit(5).all()
    
    grafico_perdas_response = GraficoData(
        labels=[row.cidade for row in grafico_perdas_data],
        values=[float(row.total_perdas or 0.0) for row in grafico_perdas_data]
    )

    return DashboardResponse(
        cards=cards_response,
        grafico_custo_loja=grafico_custo_response,
        grafico_top_perdas=grafico_perdas_response
    )

