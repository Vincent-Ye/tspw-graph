import os

import pytest

from app.extraction.models import ExtractionRequest
from app.extraction.providers import ProviderRegistry
from app.settings import get_settings


def test_configured_model_smoke():
    provider_kind = os.getenv("RUN_MODEL_SMOKE")
    if not provider_kind:
        pytest.skip("set RUN_MODEL_SMOKE=openai or ollama")
    expected = "openai-compatible" if provider_kind == "openai" else provider_kind
    profile = next(
        (item for item in get_settings().model_profiles if item.provider == expected), None
    )
    if profile is None:
        pytest.skip(f"no {expected} model profile configured")
    if profile.api_key_env and not os.getenv(profile.api_key_env):
        pytest.skip(f"missing model secret: {profile.api_key_env}")

    result = ProviderRegistry(get_settings()).create(profile.id).extract(
        ExtractionRequest(
            project_id="smoke",
            chunk_id="smoke-1",
            text="令狐冲认识任盈盈。",
            ontology={"entity_types": ["Person"], "relation_types": ["KNOWS"]},
        )
    )
    assert result.entities
