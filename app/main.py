from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import coach, extraction, map_resistance

app = FastAPI(title="Euphoriam AI", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def optional_internal_key(request, call_next):
    if settings.ai_internal_key:
        key = request.headers.get("x-internal-key") or request.headers.get("X-Internal-Key")
        if key != settings.ai_internal_key and request.url.path != "/health":
            raise HTTPException(status_code=401, detail="Invalid internal key")
    return await call_next(request)


@app.get("/health")
def health():
    return {"ok": True, "service": "euphoriam-ai"}


app.include_router(coach.router)
app.include_router(map_resistance.router)
app.include_router(extraction.router)
