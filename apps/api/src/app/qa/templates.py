from dataclasses import dataclass


@dataclass(frozen=True)
class QueryTemplate:
    relation: str
    entity_role: str
    explanation: str
    cypher: str


RELATION_TEMPLATES = {
    "master": QueryTemplate(
        relation="MASTER_OF",
        entity_role="target",
        explanation="查找以该人物为弟子的师承事实。",
        cypher="MATCH (source:Entity)<-[:SOURCE]-(fact:Fact {project_id: $project_id, type: 'MASTER_OF'})-[:TARGET]->(target:Entity {id: $entity_id}) RETURN source, fact",
    ),
    "martial_art": QueryTemplate(
        relation="KNOWS",
        entity_role="source",
        explanation="查找该人物作为主体的武学掌握事实。",
        cypher="MATCH (source:Entity {id: $entity_id})<-[:SOURCE]-(fact:Fact {project_id: $project_id, type: 'KNOWS'})-[:TARGET]->(target:Entity) RETURN target, fact",
    ),
    "organization": QueryTemplate(
        relation="MEMBER_OF",
        entity_role="source",
        explanation="查找该人物作为主体的组织隶属事实。",
        cypher="MATCH (source:Entity {id: $entity_id})<-[:SOURCE]-(fact:Fact {project_id: $project_id, type: 'MEMBER_OF'})-[:TARGET]->(target:Entity) RETURN target, fact",
    ),
}


def classify(question: str) -> str | None:
    if "师父" in question or "師父" in question:
        return "master"
    if "武功" in question or "武学" in question or "掌握" in question:
        return "martial_art"
    if "门派" in question or "門派" in question or "属于" in question:
        return "organization"
    if question.rstrip("？?").endswith("是谁"):
        return "introduction"
    return None


def subject_text(question: str) -> str:
    text = question.strip().rstrip("？?")
    if "的" in text:
        return text.split("的", 1)[0]
    if text.endswith("是谁"):
        return text[: -len("是谁")]
    return text

