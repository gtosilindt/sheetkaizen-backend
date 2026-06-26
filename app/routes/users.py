from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from datetime import datetime, timezone
from bson import ObjectId

from app.database import db
from app.middleware.auth import get_current_user, require_admin
from app.models.user import (
    UserCreate,
    UserUpdate,
    UserPublic,
    hash_password,
    VALID_ROLES,
)

router = APIRouter()


def _user_to_public(user_doc: dict) -> UserPublic:
    """Converte doc Mongo in UserPublic."""
    return UserPublic(
        id=str(user_doc["_id"]),
        username=user_doc.get("username", ""),
        email=user_doc.get("email", ""),
        full_name=user_doc.get("full_name", ""),
        role=user_doc.get("role", "office"),
        reparto=user_doc.get("reparto"),
        linee=user_doc.get("linee", []),
        team=user_doc.get("team"),
        macchine=user_doc.get("macchine", []),
        pillar_ids=user_doc.get("pillar_ids", []),
        pillar_leader_of=user_doc.get("pillar_leader_of", []),
        foto_url=user_doc.get("foto_url"),
        job_title=user_doc.get("job_title"),
        telefono=user_doc.get("telefono"),
        is_active=user_doc.get("is_active", True),
        last_login=user_doc.get("last_login"),
    )


# ──────────────────────────────────────────
# CRUD UTENTI
# ──────────────────────────────────────────

@router.get("/")
async def list_users(
    role: Optional[str] = None,
    reparto: Optional[str] = None,
    linea: Optional[str] = None,
    pillar_id: Optional[str] = None,
    include_inactive: bool = False,
    search: Optional[str] = None,
):
    """Lista utenti con filtri (no auth required per ora - dev mode)."""
    query = {}
    if not include_inactive:
        query["is_active"] = True
    if role:
        query["role"] = role
    if reparto:
        query["reparto"] = reparto
    if linea:
        query["linee"] = linea
    if pillar_id:
        query["$or"] = [
            {"pillar_ids": pillar_id},
            {"pillar_leader_of": pillar_id},
        ]
    if search:
        query["$or"] = [
            {"full_name": {"$regex": search, "$options": "i"}},
            {"username": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
        ]

    cursor = db.users.find(query).sort("full_name", 1)
    users = await cursor.to_list(length=500)
    return [_user_to_public(u).model_dump() for u in users]


@router.get("/{user_id}")
async def get_user(user_id: str):
    """Dettaglio utente."""
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(404, "Utente non trovato")
    return _user_to_public(user).model_dump()


@router.put("/{user_id}")
async def update_user(user_id: str, payload: UserUpdate):
    """Aggiorna utente."""
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(404, "Utente non trovato")

    updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}

    # Verifica ruolo valido se presente
    if "role" in updates and updates["role"] not in VALID_ROLES:
        raise HTTPException(400, f"Ruolo non valido. Validi: {VALID_ROLES}")

    # 🆕 HASH password se presente (cambio password)
    if "password" in updates:
        new_password = updates.pop("password")
        if new_password:  # solo se non vuota
            if len(new_password) < 4:
                raise HTTPException(400, "Password troppo corta (min 4 caratteri)")
            updates["password_hash"] = hash_password(new_password)

    updates["updated_at"] = datetime.now(timezone.utc)

    await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": updates})
    updated = await db.users.find_one({"_id": ObjectId(user_id)})
    return _user_to_public(updated).model_dump()


@router.delete("/{user_id}")
async def delete_user(user_id: str):
    """Disattiva utente (NON elimina, per audit)."""
    result = await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc)}},
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Utente non trovato")
    return {"success": True, "message": "Utente disattivato"}


# ──────────────────────────────────────────
# DEMO QUICK-SWITCH (senza password, solo per demo)
# ──────────────────────────────────────────

@router.post("/switch/{username}")
async def switch_user(username: str):
    """
    Per modalità demo: switch utente attivo senza password.
    NON usare in produzione.
    """
    user = await db.users.find_one({"username": username, "is_active": True})
    if not user:
        raise HTTPException(404, "Utente non trovato")
    return {
        "user": _user_to_public(user).model_dump(),
        "token": f"demo-token-{str(user['_id'])}",
    }
