from app.extraction.models import (
    CandidateEntity,
    CandidateEvidence,
    CandidateFact,
    ExtractionRequest,
    ExtractionResult,
)


class FixedProvider:
    def __init__(self, result: ExtractionResult | None = None) -> None:
        self.result = result

    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        result = self.result or self._fixture_result(request.text)
        result.validate_for_chunk(request.text)
        return result.model_copy(deep=True)

    @staticmethod
    def _fixture_result(text: str) -> ExtractionResult:
        quote = "测试人物甲认识测试人物乙"
        start = text.find(quote)
        if start < 0:
            return ExtractionResult()
        return ExtractionResult(
            entities=[
                CandidateEntity(local_id="person-a", name="测试人物甲", type="Person"),
                CandidateEntity(local_id="person-b", name="测试人物乙", type="Person"),
            ],
            facts=[CandidateFact(
                relation="KNOWS",
                source_local_id="person-a",
                target_local_id="person-b",
                evidence=CandidateEvidence(start=start, end=start + len(quote), quote=quote),
            )],
        )
