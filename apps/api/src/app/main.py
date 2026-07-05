from fastapi import FastAPI

app = FastAPI(title="江湖图谱 API")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

