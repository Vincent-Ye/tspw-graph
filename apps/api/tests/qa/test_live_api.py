import os

import pytest
from fastapi.testclient import TestClient


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_NEO4J_INTEGRATION") != "1",
    reason="set RUN_NEO4J_INTEGRATION=1 with Neo4j running",
)


def test_live_answer_is_explainable(client: TestClient) -> None:
    response = client.post(
        "/api/ask",
        json={"project_id": "xiaoao", "question": "令狐冲的师父是谁？"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "嶽不群" in body["answer"]
    assert body["path"]
    assert body["evidence"]
    assert "$project_id" in body["cypher_template"]


def test_live_answer_does_not_invent_unknown_fact(client: TestClient) -> None:
    response = client.post(
        "/api/ask",
        json={"project_id": "xiaoao", "question": "令狐冲的生日是哪天？"},
    )

    assert response.status_code == 200
    assert response.json()["answer"] == "图谱中暂无足够事实"
