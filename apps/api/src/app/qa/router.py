from fastapi import APIRouter, Depends

from app.graph.repository import Neo4jGraphRepository
from app.graph.router import execute, get_repository
from app.qa.models import AskRequest, AskResponse
from app.qa.service import QaService

router = APIRouter(prefix="/api/ask", tags=["qa"])


@router.post("", response_model=AskResponse)
def ask(
    request: AskRequest,
    repository: Neo4jGraphRepository = Depends(get_repository),
) -> AskResponse:
    return execute(
        lambda: QaService(repository).ask(request.project_id, request.question)
    )

