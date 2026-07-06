from app.jobs.models import Job, JobStatus, transition
from app.jobs.repository import JobRepository


class JobNotFoundError(LookupError):
    pass


class JobService:
    def __init__(self, repository: JobRepository) -> None:
        self.repository = repository

    def get(self, job_id: str) -> Job:
        job = self.repository.get(job_id)
        if job is None:
            raise JobNotFoundError(job_id)
        return job

    def pause(self, job_id: str) -> Job:
        job = self.get(job_id)
        return self.repository.set_status(job_id, transition(job.status, JobStatus.PAUSED))

    def resume(self, job_id: str) -> Job:
        job = self.get(job_id)
        return self.repository.set_status(job_id, transition(job.status, JobStatus.QUEUED))

    def cancel(self, job_id: str) -> Job:
        job = self.get(job_id)
        return self.repository.set_status(job_id, transition(job.status, JobStatus.CANCELLED))

    def retry(self, job_id: str) -> Job:
        job = self.get(job_id)
        return self.repository.set_status(job_id, transition(job.status, JobStatus.QUEUED))
