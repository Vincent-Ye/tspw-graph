from collections import Counter

from pydantic import BaseModel, Field

from app.extraction.models import ExtractionRequest
from app.extraction.normalize import normalize_chunk_result
from app.extraction.providers import ExtractionProvider, ProviderError
from app.extraction.splitter import split_document
from app.graph.importer import GraphImporter
from app.graph.models import (
    ChapterRecord, EntityRecord, EvidenceRecord, FactRecord, GraphDocument,
    ImportSummary, ProjectRecord,
)
from app.ontology.catalog import CATALOG


class QualityReport(BaseModel):
    total_chunks: int
    successful_chunks: int
    failed_chunks: int = 0
    accepted_entities: int
    accepted_facts: int
    accepted_evidence: int
    ambiguous_entities: int = 0
    rejected_by_code: dict[str, int] = Field(default_factory=dict)
    model_calls: int
    retry_count: int = 0


class PipelineResult(BaseModel):
    quality: QualityReport
    import_summary: ImportSummary


class ExtractionPipeline:
    def __init__(self, importer: GraphImporter) -> None:
        self.importer = importer

    def process(
        self,
        project_id: str,
        title: str,
        source: str,
        provider: ExtractionProvider,
    ) -> PipelineResult:
        split = split_document(source)
        entities: dict[str, EntityRecord] = {}
        evidence: dict[str, EvidenceRecord] = {}
        facts: dict[str, FactRecord] = {}
        rejections: Counter[str] = Counter()
        failed_chunks = 0
        successful_chunks = 0
        for chunk in split.chunks:
            try:
                extracted = provider.extract(
                    ExtractionRequest(
                        project_id=project_id,
                        chunk_id=chunk.id,
                        text=chunk.text,
                        ontology={
                            "entity_types": [item.id.value for item in CATALOG.entity_types],
                            "relation_types": [item.id.value for item in CATALOG.relation_types],
                        },
                    )
                )
            except ProviderError as error:
                if error.code != "MODEL_CONTENT_FILTER":
                    raise
                failed_chunks += 1
                rejections.update([error.code])
                continue
            successful_chunks += 1
            normalized = normalize_chunk_result(project_id, chunk, extracted)
            entities.update((item.id, item) for item in normalized.entities)
            evidence.update((item.id, item) for item in normalized.evidence)
            for item in normalized.facts:
                existing = facts.get(item.id)
                if existing:
                    facts[item.id] = existing.model_copy(
                        update={"evidence_ids": sorted(set(existing.evidence_ids + item.evidence_ids))}
                    )
                else:
                    facts[item.id] = item
            rejections.update(item.code for item in normalized.rejections)

        document = GraphDocument(
            project=ProjectRecord(id=project_id, title=title),
            chapters=[
                ChapterRecord(
                    id=f"{project_id}:chapter:{chapter.number}",
                    number=chapter.number,
                    title=chapter.title,
                )
                for chapter in split.chapters
            ],
            entities=list(entities.values()),
            facts=list(facts.values()),
            evidence=list(evidence.values()),
        )
        summary = self.importer.import_document(document)
        return PipelineResult(
            quality=QualityReport(
                total_chunks=len(split.chunks),
                successful_chunks=successful_chunks,
                failed_chunks=failed_chunks,
                accepted_entities=len(entities),
                accepted_facts=len(facts),
                accepted_evidence=len(evidence),
                rejected_by_code=dict(rejections),
                model_calls=len(split.chunks),
            ),
            import_summary=summary,
        )
