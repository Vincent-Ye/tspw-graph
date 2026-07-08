from app.extraction.fixed import FixedProvider
from app.extraction.models import ExtractionResult
from app.extraction.pipeline import ExtractionPipeline
from app.graph.importer import GraphImporter


class MemoryWriter:
    def __init__(self):
        self.keys = {"Entity": set(), "Fact": set(), "Evidence": set()}
    def ensure_constraints(self): pass
    def upsert_batch(self, label, rows):
        if label not in self.keys: return 0
        before = len(self.keys[label])
        self.keys[label].update(row["id"] for row in rows)
        return len(self.keys[label]) - before


def test_fixed_provider_pipeline_is_idempotent():
    result = ExtractionResult.model_validate({
        "entities": [
            {"local_id": "a", "name": "甲", "type": "Person"},
            {"local_id": "b", "name": "乙", "type": "Person"},
        ],
        "facts": [{
            "relation": "ALLY_OF", "source_local_id": "a", "target_local_id": "b",
            "evidence": {"start": 0, "end": 3, "quote": "甲识乙"}
        }],
    })
    writer = MemoryWriter()
    pipeline = ExtractionPipeline(GraphImporter(writer))
    first = pipeline.process("p-1", "测试", "第一章 开端\n甲识乙", FixedProvider(result))
    second = pipeline.process("p-1", "测试", "第一章 开端\n甲识乙", FixedProvider(result))
    assert first.quality.accepted_facts == 1
    assert first.import_summary.created_facts == 1
    assert second.import_summary.created_facts == 0


def test_pipeline_realigns_model_evidence_offsets():
    result = ExtractionResult.model_validate({
        "entities": [
            {"local_id": "a", "name": "甲", "type": "Person"},
            {"local_id": "b", "name": "乙", "type": "Person"},
        ],
        "facts": [{
            "relation": "ALLY_OF", "source_local_id": "a", "target_local_id": "b",
            "evidence": {"start": 0, "end": 3, "quote": "甲识乙"}
        }],
    })
    writer = MemoryWriter()
    pipeline = ExtractionPipeline(GraphImporter(writer))
    output = pipeline.process("p-1", "测试", "第一章 开端\n前文甲识乙", FixedProvider(result))
    assert output.quality.accepted_facts == 1
    assert output.quality.rejected_by_code == {}
