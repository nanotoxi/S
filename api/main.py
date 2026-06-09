import json
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from db.connection import db
from services.llm import llm_service
from services.embedder import embedder
from services.rag import rag_engine
from services.resume_parser import resume_parser
from api.session_manager import session_manager
from api.conversations.jd_wizard import JDWizard
from api.conversations.resume_wizard import ResumeWizard

logging.basicConfig(format="%(asctime)s %(name)s %(levelname)s %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

jd_wizard = JDWizard()
resume_wizard = ResumeWizard()

GREETING = [
    {
        "type": "bot_message",
        "content": "👋 Welcome to **Sath Bot**!\n\nI'm your AI recruitment assistant. Are you hiring, or looking for a job?",
    },
    {
        "type": "options",
        "content": "",
        "choices": [
            {"label": "I'm Hiring (Employer)", "value": "employer"},
            {"label": "I'm Job Hunting (Candidate)", "value": "candidate"},
        ],
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    logger.info("API started — DB connected.")
    yield
    await db.disconnect()
    logger.info("API stopped — DB disconnected.")


app = FastAPI(title="Sath Bot Web API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/sessions")
async def create_session():
    session = session_manager.create_session()
    return {"session_id": session.session_id}


@app.post("/api/upload/{session_id}")
async def upload_file(session_id: str, file: UploadFile = File(...)):
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    content = await file.read()
    max_bytes = int(os.getenv("MAX_FILE_SIZE_MB", 10)) * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail="File too large")

    upload_id = session_manager.store_upload(content, file.filename)
    return {"upload_id": upload_id}


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    session = session_manager.get_session(session_id)
    if not session:
        await websocket.close(code=4004)
        return

    await websocket.accept()
    for msg in GREETING:
        await websocket.send_text(json.dumps(msg))

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            msg_type = data.get("type", "text")
            # For option clicks, 'value' is the routing key; 'content' is the display label.
            # Always prefer 'value' so state machines receive the correct identifier.
            content = data.get("value") or data.get("content", "")
            upload_id = data.get("upload_id")

            responses = []

            if session.state == "ROLE_SELECT":
                if content == "employer":
                    session.role = "employer"
                    responses = [jd_wizard.start(session)]
                elif content == "candidate":
                    session.role = "candidate"
                    responses = [resume_wizard.start(session)]
                else:
                    responses = [{"type": "bot_message", "content": "Please choose Employer or Candidate to continue."}]

            elif session.role == "employer":
                responses = await jd_wizard.handle(
                    session, msg_type, content,
                    llm_service=llm_service,
                    embedder=embedder,
                    rag_engine=rag_engine,
                    db=db,
                    notifier=None,
                )

            elif session.role == "candidate":
                responses = await resume_wizard.handle(
                    session, msg_type, content,
                    upload_id=upload_id,
                    llm_service=llm_service,
                    embedder=embedder,
                    db=db,
                    resume_parser=resume_parser,
                    session_manager=session_manager,
                )

            for resp in responses:
                await websocket.send_text(json.dumps(resp))

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error [{session_id}]: {e}", exc_info=True)
        try:
            await websocket.send_text(
                json.dumps({"type": "bot_message", "content": "An error occurred. Please refresh and try again."})
            )
        except Exception:
            pass


# Serve built React frontend from web/dist if it exists
_dist = os.path.join(os.path.dirname(__file__), "..", "web", "dist")
if os.path.isdir(_dist):
    app.mount("/", StaticFiles(directory=_dist, html=True), name="frontend")
