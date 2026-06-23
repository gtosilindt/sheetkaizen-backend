from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import uuid4


class MacchinaModel(BaseModel):
    """Macchina annidata sotto una Linea."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    nome: str
    codice: Optional[str] = None
    descrizione: Optional[str] = ""
    attivo: bool = True


class LineaModel(BaseModel):
    """Linea produttiva annidata sotto un Reparto."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    nome: str
    codice: Optional[str] = None
    descrizione: Optional[str] = ""
    attivo: bool = True
    macchine: List[MacchinaModel] = []


class RepartoCreate(BaseModel):
    nome: str
    codice: Optional[str] = None
    descrizione: Optional[str] = ""
    linee: List[LineaModel] = []
    responsabile_id: Optional[str] = None
    attivo: bool = True


class RepartoUpdate(BaseModel):
    nome: Optional[str] = None
    codice: Optional[str] = None
    descrizione: Optional[str] = None
    linee: Optional[List[LineaModel]] = None
    responsabile_id: Optional[str] = None
    attivo: Optional[bool] = None
    is_active: Optional[bool] = None  # backward compat
