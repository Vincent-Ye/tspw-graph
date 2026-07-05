from app.graph.service import GraphService


class FakeRepository:
    def search(self, project_id: str, query: str, types: list[str], limit: int):
        return [
            {"id": "p1", "project_id": project_id, "type": "Person", "name": "令狐沖", "aliases": ["令狐冲"], "description": ""}
        ]


def test_search_never_returns_other_project() -> None:
    rows = GraphService(FakeRepository()).search("xiaoao", "令狐", [], 20)

    assert rows
    assert all(row.project_id == "xiaoao" for row in rows)
