from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timezone
from bson import ObjectId
import bcrypt

from app.database import get_db
from app.models.user import UserCreate, UserUpdate, UserLogin, UserPublic

router = APIRouter(prefix="/users", tags=["users"])


def get_collection():
    return get_db()["users"]


def serialize_user(user_doc) -> dict:
    """Converte un doc Mongo in dict pubblico (senza password)."""
    if not user_doc:
        return None
    return {
        "_id": str(user_doc["_id"]),
        "id": str(user_doc["_id"]),
        "username": user_doc.get("username", ""),
        "email": user_doc.get("email", ""),
        "nome": user_doc.get("nome", ""),
        "ruolo": user_doc.get("ruolo", "operator"),
        "foto_url": user_doc.get("foto_url"),
        "telefono": user_doc.get("telefono"),
        "job_title": user_doc.get("job_title"),
        "reparto": user_doc.get("reparto"),
        "linea": user_doc.get("linea"),
        "macchine": user_doc.get("macchine", []),
        "pillar_ids": user_doc.get("pillar_ids", []),
        "pillar_leader_of": user_doc.get("pillar_leader_of", []),
        "attivo": user_doc.get("attivo", True),
        "note": user_doc.get("note"),
        "created_at": user_doc.get("created_at"),
        "updated_at": user_doc.get("updated_at"),
    }


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ──────────────────────────────────────────
# CRUD UTENTI
# ──────────────────────────────────────────

@router.get("/")
async def list_users(
    ruolo: Optional[str] = None,
    reparto: Optional[str] = None,
    linea: Optional[str] = None,
    pillar_id: Optional[str] = None,
    include_inactive: bool = False,
    search: Optional[str] = None,
):
    """Lista utenti con filtri."""
    query = {}
    if not include_inactive:
        query["attivo"] = True
    if ruolo:
        query["ruolo"] = ruolo
    if reparto:
        query["reparto"] = reparto
    if linea:
        query["linea"] = linea
    if pillar_id:
        query["$or"] = [
            {"pillar_ids": pillar_id},
            {"pillar_leader_of": pillar_id},
        ]
    if search:
        query["$or"] = [
            {"nome": {"$regex": search, "$options": "i"}},
            {"username": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
        ]

    cursor = get_collection().find(query).sort("nome", 1)
    users = await cursor.to_list(length=500)
    return [serialize_user(u) for u in users]


@router.get("/{user_id}")
async def get_user(user_id: str):
    """Dettaglio utente."""
    user = await get_collection().find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(404, "Utente non trovato")
    return serialize_user(user)


@router.post("/")
async def create_user(payload: UserCreate):
    """Crea nuovo utente."""
    # Verifica username univoco
    existing = await get_collection().find_one({"username": payload.username})
    if existing:
        raise HTTPException(400, f"Username '{payload.username}' già esistente")

    # Verifica email univoca
    existing_email = await get_collection().find_one({"email": payload.email})
    if existing_email:
        raise HTTPException(400, f"Email '{payload.email}' già esistente")

    doc = payload.model_dump()
    doc["password_hash"] = hash_password(doc.pop("password"))
    doc["created_at"] = datetime.now(timezone.utc)
    doc["updated_at"] = datetime.now(timezone.utc)

    result = await get_collection().insert_one(doc)
    created = await get_collection().find_one({"_id": result.inserted_id})
    return serialize_user(created)


@router.put("/{user_id}")
async def update_user(user_id: str, payload: UserUpdate):
    """Aggiorna utente."""
    user = await get_collection().find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(404, "Utente non trovato")

    updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}

    # Se hanno cambiato password, hashala
    if "password" in updates:
        updates["password_hash"] = hash_password(updates.pop("password"))

    updates["updated_at"] = datetime.now(timezone.utc)

    await get_collection().update_one(
        {"_id": ObjectId(user_id)},
        {"$set": updates},
    )

    updated = await get_collection().find_one({"_id": ObjectId(user_id)})
    return serialize_user(updated)


@router.delete("/{user_id}")
async def delete_user(user_id: str):
    """Disattiva utente (NON elimina, per audit)."""
    result = await get_collection().update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"attivo": False, "updated_at": datetime.now(timezone.utc)}},
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Utente non trovato")
    return {"success": True, "message": "Utente disattivato"}


# ──────────────────────────────────────────
# LOGIN (simulato per ora, JWT vero in produzione)
# ──────────────────────────────────────────

@router.post("/login")
async def login_user(payload: UserLogin):
    """Login simulato: ritorna user data + fake token."""
    user = await get_collection().find_one({"username": payload.username})
    if not user:
        raise HTTPException(401, "Username o password errati")

    if not user.get("attivo", True):
        raise HTTPException(403, "Utente disattivato")

    # Verifica password
    if not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(401, "Username o password errati")

    return {
        "user": serialize_user(user),
        "token": f"fake-token-{str(user['_id'])}",  # TODO: JWT vero in produzione
    }


# ──────────────────────────────────────────
# QUICK SWITCH (modalità demo per cambiare utente)
# ──────────────────────────────────────────

@router.post("/switch/{username}")
async def switch_user(username: str):
    """Per demo: cambia utente attivo via dropdown (no password)."""
    user = await get_collection().find_one({"username": username, "attivo": True})
    if not user:
        raise HTTPException(404, "Utente non trovato")
    return {
        "user": serialize_user(user),
        "token": f"demo-token-{str(user['_id'])}",
    }
