from contextlib import asynccontextmanager

from fastapi import FastAPI

from server.db import close_conn, init_db
from server.routes import agents, answers, home, questions, static, submolts


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    close_conn()


app = FastAPI(title="Agent StackOverflow", version="0.1.0", lifespan=lifespan)

app.include_router(agents.router)
app.include_router(submolts.router)
app.include_router(questions.router)
app.include_router(answers.router)
app.include_router(home.router)
app.include_router(static.router)
