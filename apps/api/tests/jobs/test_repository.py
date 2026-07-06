from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine

from app.jobs.models import InvalidJobTransition, JobStatus, transition
from app.jobs.repository import JobRepository


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 1, 1, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, *, seconds: int) -> None:
        self.now += timedelta(seconds=seconds)


def test_illegal_transition_is_rejected():
    with pytest.raises(InvalidJobTransition):
        transition(JobStatus.COMPLETED, JobStatus.EXTRACTING)


def test_expired_lease_can_be_reclaimed():
    clock = Clock()
    repository = JobRepository(
        create_engine("sqlite+pysqlite:///:memory:"), clock=clock
    )
    job = repository.create("p-1", "fixed:test")

    assert repository.claim_next("w-1", 30).id == job.id
    assert repository.claim_next("w-2", 30) is None
    clock.advance(seconds=31)
    assert repository.claim_next("w-2", 30).id == job.id


def test_events_are_monotonic_and_filterable():
    repository = JobRepository(create_engine("sqlite+pysqlite:///:memory:"))
    job = repository.create("p-1", "fixed:test")
    repository.set_status(job.id, JobStatus.PAUSED)

    events = repository.events_after(job.id, 1)

    assert [event.sequence for event in events] == [2]
    assert events[0].snapshot["status"] == "PAUSED"
