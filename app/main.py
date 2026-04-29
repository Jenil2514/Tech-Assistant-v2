from fastapi import FastAPI, Request
from app.services.agent_service import handler

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Assistant API running"}

@app.post("/slack/events")
async def slack_events(req: Request):
    return await handler.handle(req)

@app.post("/slack/commands")
async def slack_commands(req: Request):
    return await handler.handle(req)
