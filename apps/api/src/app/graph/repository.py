from typing import Any, Protocol

from neo4j import Driver, GraphDatabase

from app.settings import Settings


class GraphRepository(Protocol):
    def search(
        self, project_id: str, query: str, types: list[str], limit: int
    ) -> list[dict[str, Any]]: ...


class Neo4jGraphRepository:
    def __init__(self, driver: Driver) -> None:
        self.driver = driver

    @classmethod
    def from_settings(cls, settings: Settings) -> "Neo4jGraphRepository":
        return cls(
            GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
            )
        )

    def close(self) -> None:
        self.driver.close()

    def search(
        self, project_id: str, query: str, types: list[str], limit: int
    ) -> list[dict[str, Any]]:
        statement = """
            MATCH (n:Entity {project_id: $project_id})
            WHERE (toLower(n.name) CONTAINS toLower($search_text)
                OR any(alias IN coalesce(n.aliases, []) WHERE toLower(alias) CONTAINS toLower($search_text)))
              AND (size($types) = 0 OR n.type IN $types)
            RETURN properties(n) AS entity
            ORDER BY CASE WHEN n.name = $search_text THEN 0 ELSE 1 END, n.name
            LIMIT $limit
        """
        return self._entities(
            statement,
            project_id=project_id,
            search_text=query,
            types=types,
            limit=limit,
        )

    def neighborhood(
        self,
        project_id: str,
        entity_id: str,
        depth: int,
        limit: int,
        from_chapter: int | None,
        to_chapter: int | None,
    ) -> dict[str, list[dict[str, Any]]]:
        statement = f"""
            MATCH p=(center:Entity {{project_id: $project_id, id: $entity_id}})
                -[rels:RELATED*1..{depth}]-(other:Entity {{project_id: $project_id}})
            WHERE all(r IN rels WHERE
                ($from_chapter IS NULL OR r.to_chapter IS NULL OR r.to_chapter >= $from_chapter)
                AND ($to_chapter IS NULL OR r.from_chapter IS NULL OR r.from_chapter <= $to_chapter))
            WITH collect(p)[..$limit] AS paths
            RETURN
                reduce(ns = [], p IN paths | ns + nodes(p)) AS nodes,
                reduce(rs = [], p IN paths | rs + relationships(p)) AS edges
        """
        with self.driver.session() as session:
            record = session.run(
                statement,
                project_id=project_id,
                entity_id=entity_id,
                limit=limit,
                from_chapter=from_chapter,
                to_chapter=to_chapter,
            ).single()
            if record is None:
                return {"nodes": [], "edges": []}
            nodes = {node["id"]: dict(node) for node in record["nodes"]}
            edges = {
                edge["id"]: {
                    **dict(edge),
                    "source_id": edge.start_node["id"],
                    "target_id": edge.end_node["id"],
                }
                for edge in record["edges"]
            }
            return {"nodes": list(nodes.values()), "edges": list(edges.values())}

    def shortest_path(
        self, project_id: str, source_id: str, target_id: str, max_depth: int
    ) -> dict[str, list[dict[str, Any]]]:
        statement = f"""
            MATCH (source:Entity {{project_id: $project_id, id: $source_id}}),
                  (target:Entity {{project_id: $project_id, id: $target_id}})
            MATCH p=shortestPath((source)-[:RELATED*..{max_depth}]-(target))
            RETURN nodes(p) AS nodes, relationships(p) AS edges
        """
        with self.driver.session() as session:
            record = session.run(
                statement,
                project_id=project_id,
                source_id=source_id,
                target_id=target_id,
            ).single()
            if record is None:
                return {"nodes": [], "edges": []}
            return {
                "nodes": [dict(node) for node in record["nodes"]],
                "edges": [
                    {
                        **dict(edge),
                        "source_id": edge.start_node["id"],
                        "target_id": edge.end_node["id"],
                    }
                    for edge in record["edges"]
                ],
            }

    def entity_detail(self, project_id: str, entity_id: str) -> dict[str, Any] | None:
        statement = """
            MATCH (entity:Entity {project_id: $project_id, id: $entity_id})
            OPTIONAL MATCH (fact:Fact)-[:SOURCE|TARGET]->(entity)
            OPTIONAL MATCH (fact)-[:SOURCE]->(source:Entity)
            OPTIONAL MATCH (fact)-[:TARGET]->(target:Entity)
            OPTIONAL MATCH (fact)-[:EVIDENCED_BY]->(evidence:Evidence)-[:IN_CHAPTER]->(chapter:Chapter)
            RETURN properties(entity) AS entity,
                collect(DISTINCT {
                    id: fact.id, type: fact.type, source_id: source.id, target_id: target.id,
                    evidence: {id: evidence.id, chapter_id: chapter.id,
                        chapter_number: chapter.number, chapter_title: chapter.title,
                        start_offset: evidence.start_offset, end_offset: evidence.end_offset,
                        quote: evidence.quote}
                }) AS rows
        """
        with self.driver.session() as session:
            record = session.run(statement, project_id=project_id, entity_id=entity_id).single()
            if record is None:
                return None
            return {"entity": record["entity"], "rows": record["rows"]}

    def timeline(
        self,
        project_id: str,
        person_id: str | None,
        from_chapter: int | None,
        to_chapter: int | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        statement = """
            MATCH (event:Entity {project_id: $project_id})-[r:RELATED]-(person:Entity {project_id: $project_id})
            WHERE event.type IN ['Event', 'TeachingEvent']
              AND ($person_id IS NULL OR person.id = $person_id)
              AND ($from_chapter IS NULL OR r.from_chapter >= $from_chapter)
              AND ($to_chapter IS NULL OR r.from_chapter <= $to_chapter)
            RETURN DISTINCT properties(event) AS event, min(r.from_chapter) AS chapter_number
            ORDER BY chapter_number, event.name
            LIMIT $limit
        """
        with self.driver.session() as session:
            return [
                {"event": record["event"], "chapter_number": record["chapter_number"]}
                for record in session.run(
                    statement,
                    project_id=project_id,
                    person_id=person_id,
                    from_chapter=from_chapter,
                    to_chapter=to_chapter,
                    limit=limit,
                )
            ]

    def entity_exists(self, project_id: str, entity_id: str) -> bool:
        with self.driver.session() as session:
            return session.run(
                "MATCH (n:Entity {project_id: $project_id, id: $entity_id}) RETURN count(n) > 0 AS found",
                project_id=project_id,
                entity_id=entity_id,
            ).single()["found"]

    def _entities(self, statement: str, **parameters: Any) -> list[dict[str, Any]]:
        with self.driver.session() as session:
            return [dict(record["entity"]) for record in session.run(statement, **parameters)]
