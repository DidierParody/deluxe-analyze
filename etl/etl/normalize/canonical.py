from pyspark.sql import Column
from pyspark.sql import functions as F
from pyspark.sql.types import (
    BooleanType,
    DateType,
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

USUARIO_SCHEMA = StructType([
    StructField("id", StringType(), False),
    StructField("telegram_id", StringType(), True),
    StructField("username", StringType(), True),
    StructField("social_role", StringType(), True),
    StructField("social_group_id", StringType(), True),
    StructField("secondary_group_id", StringType(), True),
    StructField("attendance_level", StringType(), True),
    StructField("vip_affinity", DoubleType(), True),
    StructField("invite_power", DoubleType(), True),
    StructField("table_preference", StringType(), True),
    StructField("rfm_seed_segment", StringType(), True),
    StructField("newcomer_affinity", DoubleType(), True),
    StructField("mixing_score", DoubleType(), True),
    StructField("source", StringType(), False),
])

EVENTO_SCHEMA = StructType([
    StructField("id", StringType(), False),
    StructField("name", StringType(), True),
    StructField("event_type", StringType(), True),
    StructField("expected_demand_level", StringType(), True),
    StructField("vip_pull", DoubleType(), True),
    StructField("event_date", DateType(), True),
    StructField("start_time", TimestampType(), True),
    StructField("end_time", TimestampType(), True),
    StructField("event_state_id", IntegerType(), True),
    StructField("source", StringType(), False),
])

MESA_SCHEMA = StructType([
    StructField("id", StringType(), False),
    StructField("table_number", IntegerType(), True),
    StructField("capacity", IntegerType(), True),
    StructField("is_vip", BooleanType(), True),
    StructField("event_id", StringType(), True),
    StructField("source", StringType(), False),
])

SEGMENTO_SCHEMA = StructType([
    StructField("name", StringType(), False),
    StructField("description", StringType(), True),
    StructField("source", StringType(), False),
])

ASISTIO_A_SCHEMA = StructType([
    StructField("user_id", StringType(), False),
    StructField("event_id", StringType(), False),
    StructField("ticket_tier", StringType(), True),
    StructField("source", StringType(), False),
])

RESERVO_SCHEMA = StructType([
    StructField("user_id", StringType(), False),
    StructField("table_id", StringType(), False),
    StructField("event_id", StringType(), False),
    StructField("source", StringType(), False),
])

PERTENECE_A_SCHEMA = StructType([
    StructField("user_id", StringType(), False),
    StructField("segment_name", StringType(), False),
    StructField("source", StringType(), False),
])


def add_namespace(col_name: str, prefix: str) -> Column:
    return F.concat(F.lit(f"{prefix}:"), F.col(col_name))


SCHEMA_QUERIES = [
    "CREATE CONSTRAINT usuario_id_unique IF NOT EXISTS FOR (u:Usuario) REQUIRE u.id IS UNIQUE",
    "CREATE CONSTRAINT evento_id_unique IF NOT EXISTS FOR (e:Evento) REQUIRE e.id IS UNIQUE",
    "CREATE CONSTRAINT mesa_id_unique IF NOT EXISTS FOR (m:Mesa) REQUIRE m.id IS UNIQUE",
    "CREATE CONSTRAINT segmento_name_unique IF NOT EXISTS FOR (s:Segmento) REQUIRE s.name IS UNIQUE",
    "CREATE INDEX usuario_telegram_idx IF NOT EXISTS FOR (u:Usuario) ON (u.telegram_id)",
    "CREATE INDEX evento_date_idx IF NOT EXISTS FOR (e:Evento) ON (e.event_date)",
]

CONOCE_A_CYPHER = """
MATCH (u1:Usuario)-[a1:ASISTIO_A]->(e:Evento)<-[a2:ASISTIO_A]-(u2:Usuario)
WHERE u1.id < u2.id
WITH u1, u2, count(e) AS shared_events,
     sum(CASE WHEN a1.ticket_tier = 'vip' AND a2.ticket_tier = 'vip' THEN 1 ELSE 0 END) AS shared_vip_events,
     min(e.event_date) AS first_shared_event, max(e.event_date) AS last_shared_event
OPTIONAL MATCH (u1)-[r1:RESERVO]->(:Mesa), (u2)-[r2:RESERVO]->(:Mesa)
WHERE r1.event_id = r2.event_id AND u1.id < u2.id
WITH u1, u2, shared_events, shared_vip_events, first_shared_event, last_shared_event,
     count(r1) AS shared_reservations
WHERE shared_events >= 1
MERGE (u1)-[r:CONOCE_A]-(u2)
SET r.shared_events = shared_events,
    r.shared_vip_events = shared_vip_events,
    r.shared_reservations = shared_reservations,
    r.first_shared_event = first_shared_event,
    r.last_shared_event = last_shared_event,
    r.tie_strength = round(toFloat(shared_events) + toFloat(shared_vip_events) * 0.5 + toFloat(shared_reservations) * 0.75, 3)
"""
