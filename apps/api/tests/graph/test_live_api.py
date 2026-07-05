import os

import pytest
from fastapi.testclient import TestClient


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_NEO4J_INTEGRATION") != "1",
    reason="set RUN_NEO4J_INTEGRATION=1 with Neo4j running",
)


def test_live_graph_endpoints(client: TestClient) -> None:
    urls = [
        "/api/graph/search?project_id=xiaoao&query=令狐",
        "/api/entities/xiaoao:person:linghuchong?project_id=xiaoao",
        "/api/graph/neighborhood?project_id=xiaoao&entity_id=xiaoao:person:linghuchong&depth=2",
        "/api/graph/path?project_id=xiaoao&source_id=xiaoao:person:linghuchong&target_id=xiaoao:person:fengqingyang",
        "/api/graph/timeline?project_id=xiaoao&person_id=xiaoao:person:linghuchong",
    ]

    responses = [client.get(url) for url in urls]

    assert [response.status_code for response in responses] == [200] * len(urls)
    assert responses[0].json()[0]["name"] == "令狐沖"
    assert responses[1].json()["facts"]
    assert responses[2].json()["nodes"]
    assert responses[3].json()["edges"]
    assert responses[4].json()[0]["event"]["name"] == "思過崖傳劍"
