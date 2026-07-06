from collections.abc import Callable, Mapping

from app.jobs.models import Job, JobStatus
from app.jobs.repository import JobRepository


NEXT_STATUS = {
    JobStatus.SPLITTING: JobStatus.EXTRACTING,
    JobStatus.EXTRACTING: JobStatus.RESOLVING,
    JobStatus.RESOLVING: JobStatus.VALIDATING,
    JobStatus.VALIDATING: JobStatus.IMPORTING,
    JobStatus.IMPORTING: JobStatus.COMPLETED,
}


class WorkerRunner:
    def __init__(
        self,
        repository: JobRepository,
        *,
        worker_id: str,
        handlers: Mapping[JobStatus, Callable[[Job], None]],
        lease_seconds: int = 60,
    ) -> None:
        self.repository = repository
        self.worker_id = worker_id
        self.handlers = handlers
        self.lease_seconds = lease_seconds

    def run_once(self) -> bool:
        job = self.repository.claim_next(self.worker_id, self.lease_seconds)
        if job is None:
            return False
        handler = self.handlers.get(job.status)
        if handler is None:
            self.repository.set_status(job.id, JobStatus.FAILED, error_code="STAGE_HANDLER_MISSING")
            return True
        try:
            handler(job)
            self.repository.set_status(job.id, NEXT_STATUS[job.status])
        except Exception:
            self.repository.set_status(job.id, JobStatus.FAILED, error_code="WORKER_STAGE_FAILED")
        return True
