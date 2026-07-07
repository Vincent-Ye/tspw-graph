import os

import pytest

from app.graph.importer import GraphImporter
from app.graph.models import (
    ChapterRecord,
    EntityRecord,
    EvidenceRecord,
    FactRecord,
    GraphDocument,
    ProjectRecord,
)
from app.graph.neo4j import Neo4jGraphWriter
from app.graph.repository import Neo4jGraphRepository
from app.ontology.models import EntityType, RelationType
from app.review.graph import ReviewGraphRepository
from app.settings import Settings


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_NEO4J_INTEGRATION") != "1",
    reason="set RUN_NEO4J_INTEGRATION=1 with Neo4j running",
)


def document() -> GraphDocument:
    return GraphDocument(
        project=ProjectRecord(id="review-filter", title="审核过滤测试"),
        chapters=[ChapterRecord(id="c1", number=1, title="第一章")],
        entities=[
            EntityRecord(
                id="linghu",
                type=EntityType.PERSON,
                name="令狐冲",
                aliases=["冲儿"],
            ),
            EntityRecord(id="yue", type=EntityType.PERSON, name="岳不群"),
        ],
        facts=[
            FactRecord(
                id="fact-master",
                type=RelationType.MASTER_OF,
                source_id="yue",
                target_id="linghu",
                evidence_ids=["ev1"],
                confidence=0.4,
            )
        ],
        evidence=[
            EvidenceRecord(
                id="ev1",
                chapter_id="c1",
                start_offset=0,
                end_offset=5,
                quote="岳不群传剑",
                text_hash="h",
            )
        ],
    )


def test_rejected_fact_is_hidden_from_default_graph() -> None:
    settings = Settings()
    writer = Neo4jGraphWriter.from_settings(settings)
    writer.delete_project("review-filter")
    GraphImporter(writer).import_document(document())
    graph = Neo4jGraphRepository.from_settings(settings)
    review = ReviewGraphRepository.from_settings(settings)

    before = graph.entity_detail("review-filter", "linghu")
    assert before is not None
    assert any(row["id"] == "fact-master" for row in before["rows"])

    review.reject_fact("review-filter", "fact-master")

    after = graph.entity_detail("review-filter", "linghu")
    assert after is not None
    assert all(row["id"] != "fact-master" for row in after["rows"])


def test_merged_entity_is_hidden_from_search() -> None:
    settings = Settings()
    writer = Neo4jGraphWriter.from_settings(settings)
    writer.delete_project("review-filter")
    GraphImporter(writer).import_document(document())
    graph = Neo4jGraphRepository.from_settings(settings)
    review = ReviewGraphRepository.from_settings(settings)

    review.merge_entities("review-filter", "linghu", "yue")

    results = graph.search("review-filter", "令狐冲", [], 10)
    assert all(row["id"] != "linghu" for row in results)


def test_split_alias_removes_alias_from_source() -> None:
    settings = Settings()
    writer = Neo4jGraphWriter.from_settings(settings)
    writer.delete_project("review-filter")
    GraphImporter(writer).import_document(document())
    review = ReviewGraphRepository.from_settings(settings)
    graph = Neo4jGraphRepository.from_settings(settings)

    review.split_alias("review-filter", "linghu", "冲儿", None)

    detail = graph.entity_detail("review-filter", "linghu")
    assert detail is not None
    assert "冲儿" not in detail["entity"].get("aliases", [])
