from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
import bcrypt


# ──────────────────────────────────────────
# COSTANTI RUOLI
# ──────────────────────────────────────────

ROLE_ADMIN = "admin"
ROLE_MANAGER = "manager"
ROLE_OFFICE = "office"
ROLE_OPERATOR = "operator"

VALID_ROLES = [ROLE_ADMIN, ROLE_MANAGER, ROLE_OFFICE, ROLE_OPERATOR]


# ──────────────────────────────────────────
# FUNZIONI HELPER PASSWORD
# ──────────────────────────────────────────

def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


# ──────────────────────────────────────────
# MODELLI USER
# ──────────────────────────────────────────

class UserCreate(BaseModel):
    """Payload per registrazione nuovo utente."""
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: str = ROLE_OFFICE

    # Anagrafica produzione
    reparto: Optional[str] = None
    linee: List[str] = []
    team: Optional[str] = None
    macchine: List[str] = []

    # Pillar
    pillar_ids: List[str] = []
    pillar_leader_of: List[str] = []

    # Altri campi
    foto_url: Optional[str] = None
    telefono: Optional[str] = None
    job_title: Optional[str] = None
    note: Optional[str] = None


class UserUpdate(BaseModel):
    """Payload per update utente (tutti opzionali)."""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None

    reparto: Optional[str] = None
    linee: Optional[List[str]] = None
    team: Optional[str] = None
    macchine: Optional[List[str]] = None

    pillar_ids: Optional[List[str]] = None
    pillar_leader_of: Optional[List[str]] = None

    foto_url: Optional[str] = None
    telefono: Optional[str] = None
    job_title: Optional[str] = None

    is_active: Optional[bool] = None
    note: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    """Risposta pubblica utente."""
    id: str
    username: str
    email: str
    full_name: str
    role: str

    reparto: Optional[str] = None
    linee: List[str] = []
    team: Optional[str] = None
    macchine: List[str] = []

    pillar_ids: List[str] = []
    pillar_leader_of: List[str] = []

    foto_url: Optional[str] = None
    job_title: Optional[str] = None
    telefono: Optional[str] = None

    is_active: bool = True
    last_login: Optional[datetime] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
