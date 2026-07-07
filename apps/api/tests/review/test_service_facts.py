from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.projects.models import Base
from app.review.models import (
    ReviewActionType,
    ReviewItemStatus,
    ReviewItemType,
    ReviewSource,
)
from app.review.repository import ReviewItemCreate, ReviewRepository
from app.review.service import ReviewActionRequest, ReviewService


class FakeReviewGraph:
    def __init__(self):
        self.accepted: list[str] = []
        self.rejected: list[str] = []

    def accept_fact(self, project_id: str, fact_id: str) -> None:
        self.accepted.append(f"{project_id}:{fact_id}")

    def reject_fact(self, project_id: str, fact_id: str) -> None:
        self.rejected.append(f"{project_id}:{fact_id}")


def service():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    repo = ReviewRepository(sessionmaker(engine))
    graph = FakeReviewGraph()
    return ReviewService(repo, graph), repo, graph


def test_accept_fact_records_audit_and_resolves_item():
    svc, repo, graph = service()
    item = repo.create_item_once(
        "project-a",
        ReviewItemCreate(
            item_type=ReviewItemType.FACT,
            source=ReviewSource.RULE,
            reason_code="LOW_CONFIDENCE_FACT",
            target={"fact_id": "fact-1"},
            evidence_ids=["ev-1"],
            fingerprint="fact:fact-1:LOW_CONFIDENCE_FACT",
            severity=40,
        ),
    )

    result = svc.apply_action(
        "project-a",
        item.id,
        ReviewActionRequest(
            action_type=ReviewActionType.ACCEPT_FACT,
            payload={"fact_id": "fact-1"},
            idempotency_key="accept-fact-1",
        ),
    )

    assert result.item.status == ReviewItemStatus.RESOLVED
    assert result.action.reviewer == "local_reviewer"
    assert graph.accepted == ["project-a:fact-1"]


def test_reject_fact_is_idempotent():
    svc, repo, graph = service()
    item = repo.create_item_once(
        "project-a",
        ReviewItemCreate(
            item_type=ReviewItemType.FACT,
            source=ReviewSource.RULE,
            reason_code="LOW_CONFIDENCE_FACT",
            target={"fact_id": "fact-1"},
            evidence_ids=[],
            fingerprint="fact:fact-1",
            severity=40,
        ),
    )
    request = ReviewActionRequest(
        action_type=ReviewActionType.REJECT_FACT,
        payload={"fact_id": "fact-1"},
        idempotency_key="reject-fact-1",
    )

    first = svc.apply_action("project-a", item.id, request)
    second = svc.apply_action("project-a", item.id, request)

    assert first.action.id == second.action.id
    assert graph.rejected == ["project-a:fact-1", "project-a:fact-1"]
