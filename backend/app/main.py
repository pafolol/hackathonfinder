import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import db
from app.auth import seed_admin
from app.config import get_settings
from app.routers import auth, context, opportunities, projects, runs, users
from app.schemas import Schedule
from app.search import runner, scheduler

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with db.SessionLocal() as session:
        await seed_admin(session)
        await runner.fail_interrupted_runs(session)
        config = await runner.get_config(session)
    scheduler.scheduler.start()
    scheduler.apply_schedule(Schedule.model_validate(config.schedule or {}))
    yield
    scheduler.scheduler.shutdown(wait=False)
    await db.engine.dispose()


app = FastAPI(title="Buscador de oportunidades", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = APIRouter(prefix="/api")
for module in (auth, opportunities, projects, context, runs, users):
    api.include_router(module.router)
app.include_router(api)


@app.get("/api/health")
async def health():
    return {"ok": True}
