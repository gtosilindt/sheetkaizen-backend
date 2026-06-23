"""
🗑️ CLEANUP TEMPORANEO — Rimuovere dopo l'uso
=============================================
Endpoint per pulire le collezioni vecchie prima del refactoring Settings.
Da chiamare 1 volta via Swagger, poi cancellare questo file.
"""
from fastapi import APIRouter
from app.database import db

router = APIRouter()


@router.delete("/configurazioni")
async def cleanup_configurazioni():
    """Cancella TUTTI i record dalla collezione 'configurazioni'."""
    result = await db.configurazioni.delete_many({})
    return {
        "ok": True,
        "collezione": "configurazioni",
        "eliminati": result.deleted_count,
    }


@router.delete("/reparti")
async def cleanup_reparti():
    """Cancella TUTTI i record dalla collezione 'reparti'."""
    result = await db.reparti.delete_many({})
    return {
        "ok": True,
        "collezione": "reparti",
        "eliminati": result.deleted_count,
    }


@router.delete("/action-plans")
async def cleanup_action_plans():
    """Cancella TUTTI gli Action Plan (test data)."""
    result = await db.action_plans.delete_many({})
    return {
        "ok": True,
        "collezione": "action_plans",
        "eliminati": result.deleted_count,
    }


@router.delete("/kaizens")
async def cleanup_kaizens():
    """Cancella TUTTI i Kaizen (test data)."""
    result = await db.kaizens.delete_many({})
    return {
        "ok": True,
        "collezione": "kaizens",
        "eliminati": result.deleted_count,
    }
