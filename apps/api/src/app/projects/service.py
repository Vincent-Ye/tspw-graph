from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Protocol
from uuid import uuid4

from app.projects.files import UploadStore
from app.projects.models import Project
from app.projects.repository import ProjectRepository


class BuiltinProjectError(ValueError):
    pass


class ProjectNotFoundError(LookupError):
    pass


class GraphProjectWriter(Protocol):
    def delete_project(self, project_id: str) -> None: ...


class ProjectUploadService:
    def __init__(self, projects: ProjectRepository, uploads: UploadStore) -> None:
        self.projects = projects
        self.uploads = uploads

    def create(self, *, title: str, filename: str, stream: BinaryIO) -> Project:
        normalized_title = title.strip()
        if not 1 <= len(normalized_title) <= 300:
            raise ValueError("INVALID_PROJECT_TITLE")
        project_id = f"project-{uuid4()}"
        stored = self.uploads.save(project_id, filename, stream)
        try:
            return self.projects.create_user_project(
                project_id=project_id,
                title=normalized_title,
                source_path=str(stored.path.relative_to(self.uploads.root)),
                source_sha256=stored.sha256,
                source_encoding=stored.encoding,
                source_size=stored.size_bytes,
            )
        except Exception:
            self.uploads.delete_project(project_id)
            raise


class ProjectService:
    def __init__(
        self,
        projects: ProjectRepository,
        uploads: UploadStore,
        graph: GraphProjectWriter,
    ) -> None:
        self.projects = projects
        self.uploads = uploads
        self.graph = graph

    def list(self) -> list[Project]:
        return self.projects.list_projects()

    def get(self, project_id: str) -> Project:
        project = self.projects.get(project_id)
        if project is None:
            raise ProjectNotFoundError(project_id)
        return project

    def delete(self, project_id: str) -> None:
        project = self.projects.get(project_id)
        if project is None:
            return
        if project.is_builtin:
            raise BuiltinProjectError(project_id)
        self.graph.delete_project(project_id)
        self.uploads.delete_project(project_id)
        self.projects.delete(project_id)
