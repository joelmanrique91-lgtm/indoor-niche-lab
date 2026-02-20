from fastapi import APIRouter, HTTPException

from app.repositories import get_stage_by_slug, list_products, list_stages

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/health")
def api_health():
    return {"ok": True}


@router.get("/stages")
def api_stages():
    return list_stages()


@router.get("/stages/{slug}")
def api_stage_detail(slug: str):
    stage = get_stage_by_slug(slug)
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")
    return stage


@router.get("/products")
def api_products():
    return list_products()
