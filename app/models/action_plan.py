from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


# ============================================================
# TIPI (str per supportare valori dinamici configurabili dalle Settings)
# ============================================================
TIPO_AP = str
PRIORITA = str
STATO = str


# ============================================================
# SUB-MODELS
# ============================================================
class ChecklistItem(BaseModel):
    id: Optional[str] = None
    testo: str
    completato: bool = False
    completato_da: Optional[str] = None
    completato_at: Optional[datetime] = None


class Commento(BaseModel):
    id: Optional[str] = None
    autore: str
    autore_avatar: Optional[str] = None
    testo: str
    mentions: List[str] = []
    timestamp: Optional[datetime] = None
    edited_at: Optional[datetime] = None
    reactions: List[dict] = []  # [{emoji, users:[]}]


class Allegato(BaseModel):
    tipo: Literal["image", "file", "link"]
    url: str
    nome: str
    size: Optional[int] = None
    uploaded_by: Optional[str] = None
    uploaded_at: Optional[datetime] = None


class LinkEntita(BaseModel):
    """Link polimorfico verso qualsiasi entita dell'app."""
    entity_type: Literal["kaizen", "documento", "dashboard", "action_plan", "url"]
    entity_id: str
    entity_label: Optional[str] = None
    link_type: Optional[str] = "related_to"


# ============================================================
# CREATE
# ============================================================
class ActionPlanCreate(BaseModel):
    titolo: str
    descrizione: Optional[str] = ""
    
    # === CLASSIFICAZIONE (configurabili da Settings) ===
    tipo: Optional[TIPO_AP] = "Task"
    priorita: Optional[PRIORITA] = "Medium"
    stato: Optional[STATO] = "Da Valutare"
    categoria_perdita: Optional[str] = None       # 🆕 ex tipo_perdita (rinominato)
    
    # === HARD-CODED ===
    quinta_m: Optional[Literal["Machine", "Manodopera", "Metodo", "Materiale", "Misurazione"]] = None  # 🆕 5M Ishikawa
    
    # === CONTESTO / PARENT ENTITY ===
    parent_type: Optional[Literal["kaizen", "pillar", "dashboard", "standalone"]] = "standalone"  # 🆕
    parent_id: Optional[str] = None               # ID del Kaizen/Pillar/Dashboard padre
    parent_label: Optional[str] = None            # 🆕 Nome leggibile (es. "KAI-0005", "FI", "PCS")
    pillar_id: Optional[str] = None               # 🆕 Pillar (sempre valorizzato anche transitively da Kaizen)
    dashboard_id: Optional[str] = None            # 🆕 Dashboard di appartenenza
    
    # === LEGACY (manteniamo per backward compat, ma deprecato) ===
    kaizen_id: Optional[str] = None               # ⚠️ Deprecato: usa parent_type=kaizen + parent_id
    categoria: Optional[str] = None               # ⚠️ Deprecato: usa categoria_perdita
    tipo_perdita: Optional[str] = None            # ⚠️ Deprecato: rinominato categoria_perdita
    
    # Tags & mentions
    tags: List[str] = []
    mentions: List[str] = []
    
    # Assignment
    responsabile: Optional[str] = None
    responsabile_email: Optional[str] = None
    reporter: Optional[str] = None
    watchers: List[str] = []
    
    # Location
    reparto: Optional[str] = None
    linea: Optional[str] = None
    macchina: Optional[str] = None
    
    # Dates
    data_inizio: Optional[datetime] = None
    data_scadenza: Optional[datetime] = None
    
    # Hierarchy
    parent_id: Optional[str] = None
    
    # Polymorphic links
    links: List[LinkEntita] = []
    
    # Initial checklist
    checklist: List[ChecklistItem] = []


# ============================================================
# UPDATE
# ============================================================
class ActionPlanUpdate(BaseModel):
    titolo: Optional[str] = None
    descrizione: Optional[str] = None
    
    # Classificazione
    tipo: Optional[TIPO_AP] = None
    priorita: Optional[PRIORITA] = None
    stato: Optional[STATO] = None
    categoria_perdita: Optional[str] = None       # 🆕 ex tipo_perdita
    quinta_m: Optional[Literal["Machine", "Manodopera", "Metodo", "Materiale", "Misurazione"]] = None  # 🆕
    
    # Contesto
    parent_type: Optional[Literal["kaizen", "pillar", "dashboard", "standalone"]] = None  # 🆕
    parent_id: Optional[str] = None               # 🆕
    parent_label: Optional[str] = None            # 🆕
    pillar_id: Optional[str] = None               # 🆕
    dashboard_id: Optional[str] = None            # 🆕
    
    # Legacy
    categoria: Optional[str] = None               # ⚠️ Deprecato
    tipo_perdita: Optional[str] = None            # ⚠️ Deprecato
    kaizen_id: Optional[str] = None               # ⚠️ Deprecato
    
    tags: Optional[List[str]] = None
    mentions: Optional[List[str]] = None
    
    responsabile: Optional[str] = None
    responsabile_email: Optional[str] = None
    reporter: Optional[str] = None
    watchers: Optional[List[str]] = None
    
    reparto: Optional[str] = None
    linea: Optional[str] = None
    macchina: Optional[str] = None
    
    data_inizio: Optional[datetime] = None
    data_scadenza: Optional[datetime] = None
    
    avanzamento: Optional[int] = None
    
    is_blocked: Optional[bool] = None
    blocking_reason: Optional[str] = None
