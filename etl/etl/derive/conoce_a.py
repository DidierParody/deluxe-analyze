from neo4j import Driver

from etl.normalize.canonical import CONOCE_A_CYPHER


def derive_conoce_a(neo4j_driver: Driver) -> None:
    with neo4j_driver.session() as session:
        session.execute_write(lambda tx: tx.run(CONOCE_A_CYPHER))
