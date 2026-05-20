"""Endpoint tests with mocked Neo4j layer."""


def test_healthz_no_auth(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_users_requires_api_key(client):
    res = client.get("/users")
    assert res.status_code == 401


def test_users_returns_list(client, auth_headers):
    client.mock_run.return_value = [
        {"id": "csv:1", "username": "Aiden"},
        {"id": "csv:2", "username": "Valeria"},
    ]
    res = client.get("/users", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert len(body["users"]) == 2
    assert body["users"][0] == {"id": "csv:1", "username": "Aiden"}


def test_promo_reach(client, auth_headers):
    client.mock_run.return_value = [
        {"username": "Raúl", "hop1": 132, "hop2": 178, "hop3": 29, "total_users": 360}
    ]
    res = client.get("/promo-reach/csv:87", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["total_reach"] == 339
    assert body["reach_percentage"] == 94.17
    assert body["by_hop"] == [
        {"hop": 1, "count": 132},
        {"hop": 2, "count": 178},
        {"hop": 3, "count": 29},
    ]


def test_promo_reach_user_not_found(client, auth_headers):
    client.mock_exists.return_value = False
    res = client.get("/promo-reach/csv:99999", headers=auth_headers)
    assert res.status_code == 404


def test_influencers(client, auth_headers):
    client.mock_run.return_value = [
        {"user_id": "csv:46", "username": "Florencia", "score": 2.38},
        {"user_id": "csv:164", "username": "Mía Clara", "score": 2.36},
    ]
    res = client.get("/influencers?limit=2", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["max_score"] == 2.38
    assert body["ranking"][0]["rank"] == 1
    assert body["ranking"][1]["user_id"] == "csv:164"


def test_event_recommendations(client, auth_headers):
    client.mock_run.return_value = [
        {
            "username": "Raúl",
            "event_id": "csv:6",
            "event_name": "Noche Deluxe 6",
            "score": 720.5,
            "friends_attended": 129,
        }
    ]
    res = client.get("/event-recommendations/csv:87", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["username"] == "Raúl"
    assert body["recommendations"][0]["event_name"] == "Noche Deluxe 6"


def test_communities_buckets_niches(client, auth_headers):
    client.mock_run.return_value = [
        {"communityId": 266, "users": ["csv:1", "csv:2"], "size": 98},
        {"communityId": 1, "users": ["csv:3"], "size": 1},
        {"communityId": 2, "users": ["csv:4"], "size": 1},
    ]
    res = client.get("/communities?min_size=2", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["total_communities"] == 3
    assert len(body["dominant_communities"]) == 1
    assert body["niches_count"] == 2
    assert body["niches_total_members"] == 2


def test_brokers(client, auth_headers):
    client.mock_run.return_value = [
        {"user_id": "csv:250", "username": "X", "score": 341.85},
    ]
    res = client.get("/brokers?limit=1", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["ranking"][0]["betweenness_score"] == 341.85
