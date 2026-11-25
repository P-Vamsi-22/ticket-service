def test_create_user(client):
    resp = client.post("/users", json={"name": "Ada", "email": "ada@example.com"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Ada"
    assert data["email"] == "ada@example.com"
    assert data["id"] == 1


def test_create_user_duplicate_email(client):
    client.post("/users", json={"name": "Ada", "email": "ada@example.com"})
    resp = client.post("/users", json={"name": "Ada2", "email": "ada@example.com"})
    assert resp.status_code == 409
    assert resp.json()["status"] == 409


def test_create_user_invalid_email(client):
    resp = client.post("/users", json={"name": "Ada", "email": "not-an-email"})
    assert resp.status_code == 422
    assert resp.json()["status"] == 422


def test_get_user(client):
    created = client.post("/users", json={"name": "Ada", "email": "ada@example.com"}).json()
    resp = client.get(f"/users/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["email"] == "ada@example.com"


def test_get_user_not_found(client):
    resp = client.get("/users/999")
    assert resp.status_code == 404
    body = resp.json()
    assert body["status"] == 404
    assert "999" in body["detail"]
