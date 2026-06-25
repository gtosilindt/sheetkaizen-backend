from fastapi import APIRouter, HTTPException, Query
from app.database import db
from app.models.configurazione import ConfigurazioneCreate, ConfigurazioneUpdate, RiordinaPayload
from bson import ObjectId
from datetime import datetime, timezone
from typing import Optional
import re

router = APIRouter()


# ============================================================
# UTILS
# ============================================================
def serialize(doc: dict) -> dict:
    """Serializza ObjectId in stringa."""
    if not doc:
        return doc
    doc["_id"] = str(doc["_id"])
    if doc.get("parent_id"):
        doc["parent_id"] = str(doc["parent_id"])
    return doc


def slugify(text: str) -> str:
    """Trasforma 'Confezionamento A' → 'CONFEZ-A'."""
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text).upper()
    words = text.split()
    if not words:
        return "ITEM"
    if len(words) >= 2:
        return f"{words[0][:6]}-{words[1][:3]}"
    return words[0][:8]


async def get_unique_codice(tipo: str, base: str, exclude_id: Optional[str] = None) -> str:
    """Garantisce univocità del codice all'interno del tipo."""
    codice = base
    counter = 1
    while True:
        query = {"tipo": tipo, "codice": codice}
        if exclude_id:
            query["_id"] = {"$ne": ObjectId(exclude_id)}
        existing = await db.configurazioni.find_one(query)
        if not existing:
            return codice
        codice = f"{base}-{counter}"
        counter += 1


# ============================================================
# LIST per tipo
# ============================================================
@router.get("/")
async def list_configurazioni(
    tipo: str = Query(..., description="Tipo configurazione"),
    parent_id: Optional[str] = Query(None),
    attivo: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
):
    """Lista voci configurazione per un tipo. Restituisce array vuoto se nessuna."""
    query = {"tipo": tipo}
    if parent_id is not None:
        query["parent_id"] = parent_id if parent_id != "null" else None
    if attivo is not None:
        query["attivo"] = attivo
    if search:
        query["$or"] = [
            {"label": {"$regex": search, "$options": "i"}},
            {"codice": {"$regex": search, "$options": "i"}},
            {"descrizione": {"$regex": search, "$options": "i"}},
        ]
    
    items = []
    cursor = db.configurazioni.find(query).sort([("ordine", 1), ("label", 1)])
    async for d in cursor:
        items.append(serialize(d))
    return items


@router.get("/all")
async def list_all_configurazioni():
    """Restituisce TUTTE le configurazioni attive raggruppate per tipo.
    Per caricamento globale frontend (popolare tendine)."""
    result = {}
    cursor = db.configurazioni.find({"attivo": True}).sort([("tipo", 1), ("ordine", 1)])
    async for d in cursor:
        tipo = d["tipo"]
        if tipo not in result:
            result[tipo] = []
        result[tipo].append(serialize(d))
    return result


@router.get("/stats")
async def get_stats():
    """Conta voci per tipo (per badge nei tab)."""
    pipeline = [
        {"$group": {
            "_id": "$tipo",
            "totale": {"$sum": 1},
            "attive": {"$sum": {"$cond": ["$attivo", 1, 0]}}
        }}
    ]
    result = {}
    async for item in db.configurazioni.aggregate(pipeline):
        result[item["_id"]] = {"totale": item["totale"], "attive": item["attive"]}
    return result


@router.get("/{conf_id}")
async def get_configurazione(conf_id: str):
    doc = await db.configurazioni.find_one({"_id": ObjectId(conf_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Configurazione non trovata")
    return serialize(doc)


# ============================================================
# CREATE
# ============================================================
@router.post("/")
async def create_configurazione(conf: ConfigurazioneCreate):
    # Auto-genera codice se non fornito
    codice = conf.codice or slugify(conf.label)
    codice = await get_unique_codice(conf.tipo, codice)
    
    # Auto-calcola ordine
    if not conf.ordine:
        max_doc = await db.configurazioni.find_one(
            {"tipo": conf.tipo}, sort=[("ordine", -1)]
        )
        ordine = (max_doc.get("ordine", 0) + 1) if max_doc else 1
    else:
        ordine = conf.ordine
    
    doc = {
        "tipo": conf.tipo,
        "codice": codice,
        "label": conf.label,
        "descrizione": conf.descrizione or "",
        "icon": conf.icon,
        "color": conf.color,
        "parent_id": conf.parent_id,
        "parent_tipo": conf.parent_tipo,
        "ordine": ordine,
        "attivo": conf.attivo if conf.attivo is not None else True,
        "is_terminal": conf.is_terminal or False,
        "metadata": conf.metadata or {},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "created_by": "Default User",
    }
    result = await db.configurazioni.insert_one(doc)
    created = await db.configurazioni.find_one({"_id": result.inserted_id})
    return serialize(created)


# ============================================================
# UPDATE
# ============================================================
@router.put("/{conf_id}")
async def update_configurazione(conf_id: str, update: ConfigurazioneUpdate):
    existing = await db.configurazioni.find_one({"_id": ObjectId(conf_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Configurazione non trovata")
    
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    
    # Se cambia il codice, verifica univocità
    if "codice" in update_data and update_data["codice"] != existing.get("codice"):
        update_data["codice"] = await get_unique_codice(
            existing["tipo"], update_data["codice"], exclude_id=conf_id
        )
    
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    await db.configurazioni.update_one(
        {"_id": ObjectId(conf_id)},
        {"$set": update_data}
    )
    
    updated = await db.configurazioni.find_one({"_id": ObjectId(conf_id)})
    return serialize(updated)


# ============================================================
# RIORDINA (drag&drop batch)
# ============================================================
@router.post("/riordina")
async def riordina_configurazioni(payload: RiordinaPayload):
    for item in payload.items:
        await db.configurazioni.update_one(
            {"_id": ObjectId(item["id"])},
            {"$set": {"ordine": item["ordine"], "updated_at": datetime.now(timezone.utc)}}
        )
    return {"message": f"{len(payload.items)} elementi riordinati"}


# ============================================================
# TOGGLE attivo/inattivo
# ============================================================
@router.patch("/{conf_id}/toggle")
async def toggle_attivo(conf_id: str):
    doc = await db.configurazioni.find_one({"_id": ObjectId(conf_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Non trovata")
    nuovo_stato = not doc.get("attivo", True)
    await db.configurazioni.update_one(
        {"_id": ObjectId(conf_id)},
        {"$set": {"attivo": nuovo_stato, "updated_at": datetime.now(timezone.utc)}}
    )
    return {"attivo": nuovo_stato}


# ============================================================
# DELETE
# ============================================================
@router.delete("/{conf_id}")
async def delete_configurazione(conf_id: str):
    """Elimina solo se non ci sono figli."""
    doc = await db.configurazioni.find_one({"_id": ObjectId(conf_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Non trovata")
    
    children = await db.configurazioni.count_documents({"parent_id": conf_id})
    if children > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Ha {children} elementi figli. Eliminali prima o usa Toggle Attivo."
        )
    
    await db.configurazioni.delete_one({"_id": ObjectId(conf_id)})
    return {"message": "Eliminata"}
