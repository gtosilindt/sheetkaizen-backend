from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime


# Tipologie supportate dal sistema Settings
TIPO_CONFIG = Literal[
    "reparti",
    "linee",
    "macchine",
    "tipi_kaizen",
    "categorie_action_plan",
    "tipi_action_plan",
    "categorie_documento",
    "argomenti",
    "categorie_perdita",
    "tipi_perdita",
]


class ConfigurazioneCreate(BaseModel):
    tipo: TIPO_CONFIG
    label: str
    codice: Optional[str] = None
    descrizione: Optional[str] = ""
    icon: Optional[str] = None
    color: Optional[str] = None
    parent_id: Optional[str] = None
    parent_tipo: Optional[str] = None
    ordine: Optional[int] = 0
    attivo: Optional[bool] = True
    metadata: Optional[dict] = {}


class ConfigurazioneUpdate(BaseModel):
    label: Optional[str] = None
    codice: Optional[str] = None
    descrizione: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    parent_id: Optional[str] = None
    parent_tipo: Optional[str] = None
    ordine: Optional[int] = None
    attivo: Optional[bool] = None
    metadata: Optional[dict] = None


class RiordinaPayload(BaseModel):
    """Per drag&drop riordino: lista di {id, ordine}"""
    items: list[dict]
