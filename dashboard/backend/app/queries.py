"""Cypher queries for the dashboard endpoints — verified against production Neo4j 5.26 / GDS 2.14."""

# /users
LIST_USERS = """
MATCH (u:Usuario)
RETURN u.id AS id, u.username AS username
ORDER BY u.id
LIMIT $limit
"""

# /promo-reach/{user_id} — total reachable and breakdown per hop (1..3)
PROMO_REACH = """
MATCH (u:Usuario {id: $user_id})
OPTIONAL MATCH (u)-[:CONOCE_A]-(h1:Usuario)
WITH u, collect(DISTINCT h1) AS h1_users
OPTIONAL MATCH (u)-[:CONOCE_A*2]-(v2:Usuario)
WHERE v2 <> u AND NOT v2 IN h1_users
WITH u, h1_users, collect(DISTINCT v2) AS h2_users
OPTIONAL MATCH (u)-[:CONOCE_A*3]-(v3:Usuario)
WHERE v3 <> u AND NOT v3 IN h1_users AND NOT v3 IN h2_users
WITH u, h1_users, h2_users, collect(DISTINCT v3) AS h3_users
MATCH (total:Usuario)
RETURN
  u.username AS username,
  size(h1_users) AS hop1,
  size(h2_users) AS hop2,
  size(h3_users) AS hop3,
  count(DISTINCT total) AS total_users
"""

# /influencers — PageRank weighted by tie_strength
INFLUENCERS = """
CALL gds.pageRank.stream($graph, {relationshipWeightProperty: 'tie_strength'})
YIELD nodeId, score
RETURN
  gds.util.asNode(nodeId).id AS user_id,
  gds.util.asNode(nodeId).username AS username,
  score
ORDER BY score DESC
LIMIT $limit
"""

# /event-recommendations/{user_id}
EVENT_RECOMMENDATIONS = """
MATCH (u:Usuario {id: $user_id})-[r:CONOCE_A]-(friend:Usuario)-[:ASISTIO_A]->(e:Evento)
WHERE NOT (u)-[:ASISTIO_A]->(e)
WITH u, e, sum(r.tie_strength) AS score, count(DISTINCT friend) AS friends_attended
RETURN
  u.username AS username,
  e.id AS event_id,
  e.name AS event_name,
  score,
  friends_attended
ORDER BY score DESC, friends_attended DESC
LIMIT $limit
"""

# /communities — Louvain
COMMUNITIES = """
CALL gds.louvain.stream($graph)
YIELD nodeId, communityId
WITH communityId, collect(gds.util.asNode(nodeId).id) AS users, count(*) AS size
RETURN communityId, users, size
ORDER BY size DESC
"""

# /brokers — Betweenness centrality
BROKERS = """
CALL gds.betweenness.stream($graph, {relationshipWeightProperty: 'tie_strength'})
YIELD nodeId, score
RETURN
  gds.util.asNode(nodeId).id AS user_id,
  gds.util.asNode(nodeId).username AS username,
  score
ORDER BY score DESC
LIMIT $limit
"""
