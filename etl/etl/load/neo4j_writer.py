from neo4j import GraphDatabase
from pyspark.sql import DataFrame

from etl.normalize.canonical import SCHEMA_QUERIES


class Neo4jWriter:
    def __init__(self, uri: str, user: str, password: str, database: str) -> None:
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def setup_schema(self) -> None:
        with self._driver.session(database=self.database) as session:
            for query in SCHEMA_QUERIES:
                session.run(query)

    def write_nodes(self, df: DataFrame, label: str, id_field: str = "id") -> None:
        (
            df.write.format("org.neo4j.spark.DataSource")
            .option("url", self.uri)
            .option("authentication.basic.username", self.user)
            .option("authentication.basic.password", self.password)
            .option("labels", f":{label}")
            .option("node.keys", id_field)
            .mode("Overwrite")
            .save()
        )

    def write_relationship(
        self,
        df: DataFrame,
        rel_type: str,
        source_label: str,
        target_label: str,
        source_key: str,
        target_key: str,
    ) -> None:
        (
            df.write.format("org.neo4j.spark.DataSource")
            .option("url", self.uri)
            .option("authentication.basic.username", self.user)
            .option("authentication.basic.password", self.password)
            .option("relationship", rel_type)
            .option("relationship.save.strategy", "keys")
            .option("relationship.source.labels", f":{source_label}")
            .option("relationship.source.node.keys", f"{source_key}:id")
            .option("relationship.target.labels", f":{target_label}")
            .option("relationship.target.node.keys", f"{target_key}:id")
            .mode("Overwrite")
            .save()
        )

    def run_cypher(self, cypher: str) -> None:
        with self._driver.session(database=self.database) as session:
            session.execute_write(lambda tx: tx.run(cypher))

    def close(self) -> None:
        self._driver.close()
