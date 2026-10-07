async def test_requires_login(anon):
    for path in ("/api/opportunities", "/api/projects", "/api/context", "/api/runs", "/api/users"):
        assert (await anon.get(path)).status_code == 401


async def test_login_rejects_bad_password(anon):
    response = await anon.post("/api/auth/login", json={"email": "admin@tec.mx", "password": "incorrecta"})
    assert response.status_code == 401


async def test_me_and_logout(client):
    me = await client.get("/api/auth/me")
    assert me.json()["role"] == "admin"
    await client.post("/api/auth/logout")
    assert (await client.get("/api/auth/me")).status_code == 401


async def test_project_crud(client):
    created = await client.post(
        "/api/projects",
        json={"name": "  AgroSense ", "description": "Sensores IoT", "technologies": ["IoT", " "], "stage": ""},
    )
    assert created.status_code == 201
    project = created.json()
    assert project["name"] == "AgroSense"
    assert project["technologies"] == ["IoT"]
    assert project["stage"] is None

    updated = await client.put(f"/api/projects/{project['id']}", json={"name": "AgroSense", "is_active": False})
    assert updated.json()["is_active"] is False
    assert len((await client.get("/api/projects")).json()) == 1

    assert (await client.delete(f"/api/projects/{project['id']}")).status_code == 204
    assert (await client.get("/api/projects")).json() == []


async def test_context_roundtrip(client):
    initial = (await client.get("/api/context")).json()
    assert initial["preferences"]["deadline_window_days"] == 120

    body = {
        "profile_text": "Emprendimiento Tec GDL",
        "preferences": {**initial["preferences"], "keywords": ["IA", "agrotech"], "min_prize_usd": 500},
        "schedule": {"enabled": False, "frequency": "weekly", "weekday": 2, "hour": 9, "timezone": "America/Mexico_City"},
    }
    saved = await client.put("/api/context", json=body)
    assert saved.status_code == 200
    again = (await client.get("/api/context")).json()
    assert again["profile_text"] == "Emprendimiento Tec GDL"
    assert again["preferences"]["keywords"] == ["IA", "agrotech"]
    assert again["schedule"]["weekday"] == 2

    body["schedule"]["timezone"] = "Marte/Olimpo"
    assert (await client.put("/api/context", json=body)).status_code == 422


async def test_users_admin_only(client, anon):
    created = await client.post(
        "/api/users", json={"email": "Staff@tec.mx", "name": "Staff", "password": "otra-contraseña"}
    )
    assert created.status_code == 201
    assert created.json()["email"] == "staff@tec.mx"
    duplicate = await client.post(
        "/api/users", json={"email": "staff@tec.mx", "name": "Otro", "password": "otra-contraseña"}
    )
    assert duplicate.status_code == 409

    me = (await client.get("/api/auth/me")).json()
    assert (await client.patch(f"/api/users/{me['id']}", json={"is_active": False})).status_code == 400

    await client.post("/api/auth/logout")
    login = await client.post("/api/auth/login", json={"email": "staff@tec.mx", "password": "otra-contraseña"})
    assert login.status_code == 200
    assert (await client.get("/api/users")).status_code == 403
    assert (await client.get("/api/projects")).status_code == 200
