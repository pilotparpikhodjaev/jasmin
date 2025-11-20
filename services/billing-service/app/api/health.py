from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz", summary="Liveness probe")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}

