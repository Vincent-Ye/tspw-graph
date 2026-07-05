from fastapi import FastAPI

from app.graph.router import router as graph_router
from app.ontology.router import router as ontology_router

app = FastAPI(title="江湖图谱 API")
app.include_router(ontology_router)
app.include_router(graph_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
