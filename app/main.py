from fastapi import FastAPI, Request
from app.rag.pipeline import answer_query
from app.services.agent_service import handler

app = FastAPI()

@app.get("/")
def root():
    return {"message": "OnboardMind API running"}

@app.get("/ask")
def ask(query: str, tenant_id: str):
    response = answer_query(query, tenant_id)
    return {"answer": response}

@app.post("/slack/events")
async def slack_events(req: Request):
    return await handler.handle(req)

@app.post("/slack/commands")
async def slack_commands(req: Request):
    return await handler.handle(req)
