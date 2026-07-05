from fastapi.testclient import TestClient


def test_neighborhood_rejects_unbounded_depth(client: TestClient) -> None:
    response = client.get(
        "/api/graph/neighborhood",
        params={"project_id": "xiaoao", "entity_id": "x", "depth": 4},
    )

    assert response.status_code == 422


def test_search_rejects_excessive_limit(client: TestClient) -> None:
    response = client.get(
        "/api/graph/search",
        params={"project_id": "xiaoao", "query": "令狐", "limit": 51},
    )

    assert response.status_code == 422
