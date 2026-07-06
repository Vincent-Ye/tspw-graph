from collections.abc import Iterator
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import create_engine

from app.graph.neo4j import Neo4jGraphWriter
from app.projects.files import UploadStore
from app.projects.repository import ProjectRepository
from app.projects.service import (
    BuiltinProjectError,
    ProjectNotFoundError,
    ProjectService,
)
from app.settings import get_settings

router = APIRouter(prefix="/api/projects", tags=["projects"])


class ProjectSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    is_builtin: bool
    source_encoding: str | None
    source_size: int | None
    created_at: datetime
    updated_at: datetime


def get_project_service() -> Iterator[ProjectService]:
    settings = get_settings()
    projects = ProjectRepository(create_engine(settings.sqlite_url))
    projects.ensure_builtin_project("xiaoao", "笑傲江湖")
    graph = Neo4jGraphWriter.from_settings(settings)
    try:
        yield ProjectService(projects, UploadStore(settings.data_root), graph)
    finally:
        graph.close()


Service = Annotated[ProjectService, Depends(get_project_service)]


@router.get("", response_model=list[ProjectSummary])
def list_projects(service: Service) -> list[ProjectSummary]:
    return [ProjectSummary.model_validate(project) for project in service.list()]


@router.get("/{project_id}", response_model=ProjectSummary)
def get_project(project_id: str, service: Service) -> ProjectSummary:
    try:
        return ProjectSummary.model_validate(service.get(project_id))
    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=404, detail={"code": "PROJECT_NOT_FOUND"}
        ) from error


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: str, service: Service) -> Response:
    try:
        service.delete(project_id)
    except BuiltinProjectError as error:
        raise HTTPException(
            status_code=403, detail={"code": "BUILTIN_PROJECT_READ_ONLY"}
        ) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
