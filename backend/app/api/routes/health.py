from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/api/health", summary="Health check")
def health():
    return {"success": True, "status": "ok"}
