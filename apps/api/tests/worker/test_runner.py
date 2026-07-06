from sqlalchemy import create_engine

from app.jobs.models import JobStatus
from app.jobs.repository import JobRepository
from app.worker.runner import WorkerRunner


class Handler:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, job) -> None:
        self.calls += 1


def test_runner_does_not_repeat_completed_stage():
    repository = JobRepository(create_engine("sqlite+pysqlite:///:memory:"))
    job = repository.create("p-1", "fixed:test")
    repository.set_status(job.id, JobStatus.EXTRACTING)
    splitter = Handler()
    extractor = Handler()
    runner = WorkerRunner(
        repository,
        worker_id="w-1",
        handlers={JobStatus.SPLITTING: splitter, JobStatus.EXTRACTING: extractor},
    )

    runner.run_once()

    assert splitter.calls == 0
    assert extractor.calls == 1
    assert repository.get(job.id).status == JobStatus.RESOLVING
