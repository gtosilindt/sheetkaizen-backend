from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class DashboardCreate(BaseModel):
    nome: str
    titolo_pagina: Optional[str] = None
    descrizione: Optional[str] = None
    tipo: str = "Custom"
    reparto: Optional[str] = None
    visibilita: str = "pubblico"
    layout: List[Dict[str, Any]] = []
    utenti_autorizzati_ids: List[str] = []
    utenti_autorizzati_nomi: List[str] = []


class DashboardUpdate(BaseModel):
    nome: Optional[str] = None
    titolo_pagina: Optional[str] = None
    descrizione: Optional[str] = None
    tipo: Optional[str] = None
    reparto: Optional[str] = None
    visibilita: Optional[str] = None
    layout: Optional[List[Dict[str, Any]]] = None
    utenti_autorizzati_ids: Optional[List[str]] = None
    utenti_autorizzati_nomi: Optional[List[str]] = None
