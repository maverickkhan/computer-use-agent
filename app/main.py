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
    print(f"[SEND_MESSAGE] Starting to process message for session {session_id}")
    print(f"[SEND_MESSAGE] User input: {text}")
    
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        print(f"[SEND_MESSAGE] Session {session_id} not found")
        raise HTTPException(status_code=404, detail="Session not found")
    
    print(f"[SEND_MESSAGE] Session found. Total messages in session: {len(session.messages)}")
    
    # Save user message to database only
    print(f"[SEND_MESSAGE] Saving user message to database...")
    msg = Message(session_id=session.id, role="user", content=text)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    print(f"[SEND_MESSAGE] User message saved with ID: {msg.id}")

    # Don't call agent here - let WebSocket handle it
    print(f"[SEND_MESSAGE] User message saved. Agent processing will be handled by WebSocket.")
    
    response_data = {
        "message_id": msg.id,
        "content": msg.content,
        "timestamp": msg.timestamp,
        "status": "message_saved"
    }
    
    print(f"[SEND_MESSAGE] Returning response. Total messages in session now: {len(session.messages)}")
    print(f"[SEND_MESSAGE] Message processing completed successfully")
    
    return response_data
    
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
    print(f"[DEBUG] WebSocket connection opened for session {session_id}")
    await websocket.accept()

    # Fetch session and history, etc.
    db = next(get_db())
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        print(f"[DEBUG] Session {session_id} not found, closing WebSocket.")
        await websocket.send_json({"error": "Session not found"})
        await websocket.close()
        return

    # Get all messages except the last one (which is the agent's response)
    user_messages = [m for m in session.messages if m.role == "user"]
    if not user_messages:
        print(f"[DEBUG] No user messages found in session {session_id}")
        await websocket.close()
        return
    
    # Get the latest user message (the one that was just sent)
    latest_user_message = user_messages[-1]
    user_input = latest_user_message.content
    
    # Get previous messages for context (excluding the latest user message)
    prev_msgs = [
        {"role": m.role, "content": m.content}
        for m in session.messages
        if m.id < latest_user_message.id  # Only include messages before the current user message
    ]

    print(f"[DEBUG] Starting to stream agent response for session {session_id}")
    print(f"[DEBUG] Processing user input: {user_input}")
    
    try:
        # Use the modified run_agent_task with websocket parameter
        result = await run_agent_task(user_input, prev_msgs, websocket=websocket)
        print(f"[DEBUG] Agent task completed with result: {result}")
        
        # Save the agent's response to the database
        print(f"[DEBUG] Saving agent response to database...")
        agent_msg = Message(session_id=session.id, role="agent", content=result)
        db.add(agent_msg)
        db.commit()
        db.refresh(agent_msg)
        print(f"[DEBUG] Agent message saved with ID: {agent_msg.id}")
        
        # Send completion message
        try:
            await websocket.send_json({"type": "complete", "message": "Agent task completed"})
        except Exception as e:
            print(f"[DEBUG] Could not send completion message: {e}")
            
    except Exception as e:
        print(f"[DEBUG] Error in WebSocket streaming: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception as send_error:
            print(f"[DEBUG] Could not send error message: {send_error}")

    print(f"[DEBUG] WebSocket connection closed for session {session_id}")
    try:
        await websocket.close()
    except Exception as e:
        print(f"[DEBUG] Error closing WebSocket: {e}")

