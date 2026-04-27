from __future__ import annotations

import os

from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware

try:
    from .schemas import FilialCreate, FilialOut, FilialUpdate, NextRevisionUpdate, RevisionDatesUpdate
    from .service import RevisionService
    from .redis_store import RedisStore
    from .holidays import router as holidays_router
except ImportError:
    from schemas import FilialCreate, FilialOut, FilialUpdate, NextRevisionUpdate, RevisionDatesUpdate
    from service import RevisionService
    from redis_store import RedisStore
    from holidays import router as holidays_router


app = FastAPI(title="Revision Backend", version="1.0.0")
app.include_router(holidays_router, prefix="/api/v1", tags=["holidays"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service = RevisionService(RedisStore())


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/filials", response_model=list[FilialOut])
def list_filials() -> list[FilialOut]:
    return service.list_filials()


@app.get("/api/v1/filials/{filial_id}", response_model=FilialOut)
def get_filial(filial_id: str) -> FilialOut:
    return service.get_filial(filial_id)


@app.post("/api/v1/filials", response_model=FilialOut, status_code=status.HTTP_201_CREATED)
def create_filial(payload: FilialCreate) -> FilialOut:
    return service.create_filial(payload)


@app.put("/api/v1/filials/{filial_id}", response_model=FilialOut)
def update_filial(filial_id: str, payload: FilialUpdate) -> FilialOut:
    return service.update_filial(filial_id, payload)


@app.put("/api/v1/filials/{filial_id}/revisions", response_model=FilialOut)
def update_filial_revisions(filial_id: str, payload: RevisionDatesUpdate) -> FilialOut:
    return service.update_revision_dates(filial_id, payload)


@app.put("/api/v1/filials/{filial_id}/next-revision", response_model=FilialOut)
def update_filial_next_revision(filial_id: str, payload: NextRevisionUpdate) -> FilialOut:
    return service.update_next_revision(filial_id, payload)


@app.delete("/api/v1/filials/{filial_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_filial(filial_id: str) -> Response:
    service.delete_filial(filial_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8000"))
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
