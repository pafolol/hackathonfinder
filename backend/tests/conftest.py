import os
import tempfile

# Must be set before the app (and its engine) is imported.
_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_tmp}/test.db".replace("\\", "/")
os.environ["ADMIN_EMAIL"] = "admin@tec.mx"
os.environ["ADMIN_PASSWORD"] = "contraseña-segura"
os.environ["OPENAI_API_KEY"] = ""
os.environ["COOKIE_SECURE"] = "false"

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app import db
from app.auth import seed_admin
from app.main import app
from app.models import Base


@pytest_asyncio.fixture(autouse=True)
async def database():
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with db.SessionLocal() as session:
        await seed_admin(session)
    yield


@pytest_asyncio.fixture
async def anon():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def client(anon):
    response = await anon.post("/api/auth/login", json={"email": "admin@tec.mx", "password": "contraseña-segura"})
    assert response.status_code == 200
    yield anon
