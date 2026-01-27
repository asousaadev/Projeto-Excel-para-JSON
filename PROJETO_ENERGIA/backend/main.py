from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "API do Projeto Energia"}
# models.py
from sqlalchemy import (
    Column, Integer, String, Float, Date, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class UnidadeConsumidora(Base):
    __tablename__ = 'unidades'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255), nullable=False, index=True)  # ex: CDL ALVORADA
    grupo = Column(String(255), index=True)                 # ex: GRUPO MEDEIROS
    classe = Column(String(100))                            # ex: Comercial, Industrial
    distribuidora = Column(String(255))

    faturas = relationship("FaturaEnergia", back_populates="unidade", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_unidade_nome_grupo', 'nome', 'grupo'),
    )

class FaturaEnergia(Base):
    __tablename__ = 'faturas'
    id = Column(Integer, primary_key=True, autoincrement=True)
    unidade_id = Column(Integer, ForeignKey('unidades.id', ondelete='CASCADE'), nullable=False)
    data_referencia = Column(Date, nullable=False)  # armazenar como primeiro dia do mês para padronizar

    # Métricas de Consumo
    consumo_ponta_kwh = Column(Float, default=0.0)
    consumo_fora_ponta_kwh = Column(Float, default=0.0)
    consumo_total_kwh = Column(Float, default=0.0)

    # Métricas de Demanda
    demanda_medida_kw = Column(Float, default=0.0)
    demanda_contratada_kw = Column(Float, default=0.0)

    # Geração Distribuída (Solar)
    energia_injetada_kwh = Column(Float, default=0.0)
    saldo_acumulado_kwh = Column(Float, default=0.0)

    # Financeiro
    valor_fatura_total = Column(Float, nullable=False, default=0.0)
    custo_unitario_medio = Column(Float, default=0.0)  # calculado: valor_fatura_total / consumo_total_kwh

    unidade = relationship("UnidadeConsumidora", back_populates="faturas")

    __table_args__ = (
        UniqueConstraint('unidade_id', 'data_referencia', name='_unidade_mes_uc'),
        Index('ix_faturas_data', 'data_referencia'),
    )