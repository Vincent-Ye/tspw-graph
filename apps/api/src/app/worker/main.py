import time
from uuid import uuid4

from sqlalchemy import create_engine

from app.jobs.repository import JobRepository
from app.settings import get_settings
from app.worker.runner import WorkerRunner


def main() -> None:
    settings = get_settings()
    runner = WorkerRunner(
        JobRepository(create_engine(settings.sqlite_url)),
        worker_id=f"worker-{uuid4()}",
        handlers={},
    )
    while True:
        if not runner.run_once():
            time.sleep(1)


if __name__ == "__main__":
    main()
