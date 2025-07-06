from fastapi import FastAPI, Depends, WebSocket, HTTPException, Request
from starlette.responses import StreamingResponse
import httpx
from sqlalchemy.orm import Session as DbSession
from typing import List
from models import Session as ChatSession, Message, Base
from db import engine, get_db
from datetime import datetime
from agent import run_agent_task, run_agent_task_stream


app = FastAPI()

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"msg": "Energent AI Backend is running"}

# ---- Session Endpoints ----

@app.post("/sessions/", response_model=dict)
def create_session(db: DbSession = Depends(get_db)):
    session = ChatSession()
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"session_id": session.id, "created_at": session.created_at}

@app.get("/sessions/", response_model=List[dict])
def list_sessions(db: DbSession = Depends(get_db)):
    sessions = db.query(ChatSession).all()
    return [{"session_id": s.id, "created_at": s.created_at} for s in sessions]

@app.get("/sessions/{session_id}", response_model=dict)
def get_session(session_id: int, db: DbSession = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = [
        {"role": m.role, "content": m.content, "timestamp": m.timestamp}
        for m in session.messages
    ]
    return {
        "session_id": session.id,
        "created_at": session.created_at,
        "messages": messages
    }

# ---- Message Endpoint ----

@app.post("/sessions/{session_id}/messages", response_model=dict)
async def send_message(session_id: int, text: str, db: DbSession = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    prev_msgs = [
        {"role": m.role, "content": m.content}
        for m in session.messages
    ]
    msg = Message(session_id=session.id, role="user", content=text)
    db.add(msg)
    db.commit()
    db.refresh(msg)

    # AGENT CALL IS NOW ASYNC
    agent_reply = await run_agent_task(text, prev_msgs)
    agent_msg = Message(session_id=session.id, role="agent", content=agent_reply)
    db.add(agent_msg)
    db.commit()
    db.refresh(agent_msg)

    return {
        "message_id": msg.id,
        "content": msg.content,
        "timestamp": msg.timestamp,
        "agent_message": {
            "message_id": agent_msg.id,
            "content": agent_msg.content,
            "timestamp": agent_msg.timestamp
        }
    }
    
@app.api_route("/vnc/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])
async def proxy_vnc(request: Request, full_path: str):
    vnc_url = f"http://localhost:6080/{full_path}"
    method = request.method
    headers = dict(request.headers)
    async with httpx.AsyncClient(follow_redirects=True) as client:
        req = client.build_request(
            method,
            vnc_url,
            headers={k: v for k, v in headers.items() if k.lower() != "host"},
            content=await request.body()
        )
        upstream_response = await client.send(req, stream=True)
        response_headers = dict(upstream_response.headers)
        # Remove hop-by-hop headers
        response_headers.pop("content-encoding", None)
        return StreamingResponse(
            upstream_response.aiter_raw(),
            status_code=upstream_response.status_code,
            headers=response_headers
        )
        
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # For dev. Restrict as needed.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/sessions/{session_id}/stream")
async def stream_progress(websocket: WebSocket, session_id: int):
    await websocket.accept()

    # Fetch session and history, etc.
    db = next(get_db())
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        await websocket.send_json({"error": "Session not found"})
        await websocket.close()
        return

    prev_msgs = [
        {"role": m.role, "content": m.content}
        for m in session.messages
    ]
    user_input = prev_msgs[-1]["content"] if prev_msgs else ""

    async for block in run_agent_task_stream(user_input, prev_msgs):
        # You can send just the block, or wrap as needed
        await websocket.send_json(block)

    await websocket.close()

