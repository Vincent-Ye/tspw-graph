from app.qa.service import NO_FACTS, QaService


class Repository:
    def search(self, project_id, query, types, limit):
        return [{"id": "linghu", "name": "令狐冲", "description": "华山弟子"}]

    def entity_detail(self, project_id, entity_id):
        if entity_id == "linghu":
            return {
                "entity": {"id": "linghu", "name": "令狐冲"},
                "rows": [
                    {
                        "id": "rejected",
                        "type": "MASTER_OF",
                        "source_id": "yue",
                        "target_id": "linghu",
                        "review_status": "REJECTED",
                        "evidence": None,
                    }
                ],
            }
        return {"entity": {"id": entity_id, "name": "岳不群"}, "rows": []}


def test_qa_ignores_rejected_facts_even_if_repository_returns_them():
    response = QaService(Repository()).ask("project-a", "令狐冲的师父是谁")

    assert response.answer == NO_FACTS
