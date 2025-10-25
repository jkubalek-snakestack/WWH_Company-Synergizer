"""FastAPI entrypoint exposing synergy graph workflows."""

from __future__ import annotations

from fastapi import Body, FastAPI

from .engine import GraphEngine, DatasetPayload, PlaybookRequest


def create_app(engine: GraphEngine | None = None) -> FastAPI:
    graph_engine = engine or GraphEngine()
    app = FastAPI(title="Synergy Graph Service", version="0.2.0")

    @app.post("/recompute")
    def recompute(dataset: DatasetPayload) -> dict:
        summary = graph_engine.recompute(dataset)
        return {"ok": True, **summary}

    @app.get("/opportunities")
    def opportunities(
        orgId: str | None = None,
        companyId: str | None = None,
        status: str | None = None,
    ) -> dict:
        items = graph_engine.opportunities(org_id=orgId, company_id=companyId, status=status)
        return {"items": items, "count": len(items)}

    @app.post("/playbook")
    def playbook(payload: PlaybookRequest = Body(...)) -> dict:
        return graph_engine.playbook(payload)

    return app


app = create_app()

__all__ = ["app", "create_app"]
