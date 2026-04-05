from neo4j import GraphDatabase, Driver

# Module-level variable to hold the driver
_driver: Driver | None = None


def connect(uri: str, auth: str) -> None:
    global _driver
    username, password = auth.split("/", 1)
    _driver = GraphDatabase.driver(uri, auth=(username, password))
    _driver.verify_connectivity()


def close() -> None:
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


def get_driver() -> Driver:
    if _driver is None:
        raise RuntimeError("Neo4j driver not initialised — call connect() first")
    return _driver
