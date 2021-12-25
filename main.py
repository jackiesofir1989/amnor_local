from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn import Server, Config

from routes import route_manager
from task_manager.sch import scheduler, add_all_jobs
from utils.db import engine, Base
from utils.logging_guru import setup_logging, LOG_LEVEL

app = FastAPI(title="AmnorLED")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
route_manager.add_routes(app)


@app.on_event("startup")
async def startup_event():
    scheduler.start()
    add_all_jobs()
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.drop_all)
    #     await conn.run_sync(Base.metadata.create_all)


@app.on_event("shutdown")
async def shutdown_event():
    scheduler.remove_all_jobs()
    scheduler.shutdown()


if __name__ == '__main__':
    server = Server(Config("main:app", host='0.0.0.0', port=8000, reload=True, log_level=LOG_LEVEL, use_colors=True, ))
    setup_logging()
    server.run()
