from neo4j import Session


def search(session: Session, query: str) -> list[dict]:
    query = query.strip()
    if not query:
        return []

    label_map = {"Person": "person", "Event": "event", "Place": "place"}

    cypher = """
      CALL db.index.fulltext.queryNodes('search_index', $search_string)
      YIELD node, score
      RETURN node.uid AS uid, node.name AS name, labels(node) AS labels, score
    """
    result = session.run(cypher, search_string=f"{query}*")
    items = []
    for r in result:
        for label in r["labels"]:
            if label in label_map:
                items.append(
                    {
                        "uid": r["uid"],
                        "name": r["name"],
                        "type": label_map[label],
                        "score": r["score"],
                    }
                )
                break
    return items
