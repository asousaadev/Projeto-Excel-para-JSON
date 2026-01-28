# app/models.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric, TIMESTAMP, Date, func
from sqlalchemy.orm import relationship
from app.database import Base

# --- Modelos SQLAlchemy ---

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

    demanda_contratada_ponta_kw = Column(Numeric(10, 2))
    demanda_contratada_f_ponta_kw = Column(Numeric(10, 2))
    demanda_ponta_kw = Column(Numeric(10, 2), default=0.00)
    demanda_f_ponta_kw = Column(Numeric(10, 2), default=0.00)
    demanda_maxima_registrada_kw = Column(Numeric(10, 2), default=0.00)

    consumo_ponta_kwh = Column(Numeric(12, 2), default=0.00)
    consumo_ponta_vl = Column(Numeric(12, 2), default=0.00)
    consumo_fora_ponta_kwh = Column(Numeric(12, 2), default=0.00)
    consumo_fora_ponta_vl = Column(Numeric(12, 2), default=0.00)
    consumo_total_kwh = Column(Numeric(12, 2), default=0.00)

    valor_total_fatura = Column(Numeric(12, 2), nullable=False, default=0.00)
    valor_perdas_total = Column(Numeric(12, 2), default=0.00)

    cliente = relationship("Cliente", back_populates="faturas")
