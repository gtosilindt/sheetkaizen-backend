from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ActionPlanCreate(BaseModel):
    titolo: str
    descrizione: Optional[str] = None
    origine: str = "standalone"  # kaizen | dashboard | standalone
    origine_id: Optional[str] = None
    origine_nome: Optional[str] = None
    responsabile_nome: str
    responsabile_id: Optional[str] = None
    reparto: Optional[str] = None
    linea: Optional[str] = None
    macchina: Optional[str] = None
    categoria: Optional[str] = None
    data_scadenza: datetime
    priorita: str = "Media"  # Alta | Media | Bassa
    note: Optional[str] = None
    allegati: List[str] = []


class ActionPlanUpdate(BaseModel):
    titolo: Optional[str] = None
    descrizione: Optional[str] = None
    responsabile_nome: Optional[str] = None
    responsabile_id: Optional[str] = None
    reparto: Optional[str] = None
    linea: Optional[str] = None
    macchina: Optional[str] = None
    categoria: Optional[str] = None
    data_scadenza: Optional[datetime] = None
    data_completamento: Optional[datetime] = None
    stato: Optional[str] = None
    priorita: Optional[str] = None
    note: Optional[str] = None
    allegati: Optional[List[str]] = None
