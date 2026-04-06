import uuid

import bcrypt
from neo4j import Driver

from app.config import Settings


def run_seed(neo4j_driver: Driver, settings: Settings):

    constraint_queries = [
        "CREATE CONSTRAINT person_uid IF NOT EXISTS FOR (p:Person) REQUIRE p.uid IS UNIQUE",
        "CREATE CONSTRAINT event_uid IF NOT EXISTS FOR (e:Event) REQUIRE e.uid IS UNIQUE",
        "CREATE CONSTRAINT place_uid IF NOT EXISTS FOR (p:Place) REQUIRE p.uid IS UNIQUE",
        "CREATE CONSTRAINT image_uid IF NOT EXISTS FOR (i:Image) REQUIRE i.uid IS UNIQUE",
        "CREATE CONSTRAINT user_uid IF NOT EXISTS FOR (u:User) REQUIRE u.uid IS UNIQUE",
        "CREATE CONSTRAINT user_username IF NOT EXISTS FOR (u:User) REQUIRE u.username IS UNIQUE",
    ]
    with neo4j_driver.session() as session:
        for query in constraint_queries:
            session.run(query)

        if settings.ADMIN_USERNAME and settings.ADMIN_PASSWORD:
            admin_query = """
                MERGE (a:User {username: $admin_username})
                ON CREATE SET
                    a.uid = $uid,
                    a.hashed_password = $admin_password,
                    a.role = 'admin',
                    a.is_active = True,
                    a.created_at = timestamp(),
                    a.updated_at = timestamp()
            """
            session.run(
                admin_query,
                uid=str(uuid.uuid4()),
                admin_username=settings.ADMIN_USERNAME,
                admin_password=bcrypt.hashpw(
                    settings.ADMIN_PASSWORD.encode(), bcrypt.gensalt()
                ).decode(),
            )
