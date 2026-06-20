import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
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


@app.get("/api/admin/signups", response_class=HTMLResponse)
async def admin_signups():
    def fmt(dt):
        if dt is None:
            return "—"
        return dt.strftime("%d %b %Y, %H:%M UTC")

    def badge(text, color):
        return (
            f'<span style="background:{color}22;color:{color};border:1px solid {color}44;'
            f'padding:2px 10px;border-radius:20px;font-size:11px;white-space:nowrap">{text}</span>'
        )

    candidates = await db.fetch("""
        SELECT c.id, c.user_id, c.profile_complete, c.created_at,
               LEFT(c.resume_raw, 160) AS preview, c.resume_structured
        FROM candidates c ORDER BY c.created_at DESC
    """)
    employers = await db.fetch(
        "SELECT id, user_id, company_name, created_at FROM employers ORDER BY created_at DESC"
    )
    jds = await db.fetch("""
        SELECT j.id, j.title, j.status, LEFT(j.full_jd, 220) AS preview,
               j.created_at, e.company_name
        FROM job_descriptions j
        LEFT JOIN employers e ON e.id = j.employer_id
        ORDER BY j.created_at DESC
    """)
    users = await db.fetch(
        "SELECT id, user_type, created_at FROM users ORDER BY created_at DESC"
    )

    def candidates_rows():
        rows = ""
        for c in candidates:
            name = "—"
            try:
                rs = c["resume_structured"]
                if isinstance(rs, str):
                    rs = json.loads(rs)
                if rs:
                    name = rs.get("name") or rs.get("full_name") or "—"
            except Exception:
                pass
            preview = (c["preview"] or "").replace("<", "&lt;").replace(">", "&gt;")
            status_badge = badge("Complete", "#22c55e") if c["profile_complete"] else badge("Incomplete", "#ef4444")
            rows += f"""<tr>
              <td style="font-weight:600">{name}</td>
              <td>{status_badge}</td>
              <td style="color:#64748b;font-size:12px;max-width:320px;overflow:hidden;
                  white-space:nowrap;text-overflow:ellipsis">{preview}</td>
              <td style="color:#94a3b8;font-size:12px;white-space:nowrap">{fmt(c["created_at"])}</td>
            </tr>"""
        return rows or '<tr><td colspan="4" class="empty">No candidates yet.</td></tr>'

    def employers_rows():
        rows = ""
        for e in employers:
            rows += f"""<tr>
              <td style="font-weight:600">{e["company_name"] or "—"}</td>
              <td style="color:#94a3b8;font-size:12px;white-space:nowrap">{fmt(e["created_at"])}</td>
            </tr>"""
        return rows or '<tr><td colspan="2" class="empty">No employers yet.</td></tr>'

    def jds_rows():
        rows = ""
        for j in jds:
            preview = (j["preview"] or "").replace("<", "&lt;").replace(">", "&gt;")
            rows += f"""<tr>
              <td style="font-weight:600">{j["title"]}</td>
              <td style="color:#818cf8">{j["company_name"] or "—"}</td>
              <td>{badge(j["status"], "#22c55e")}</td>
              <td style="color:#64748b;font-size:12px;max-width:340px;overflow:hidden;
                  white-space:nowrap;text-overflow:ellipsis">{preview}</td>
              <td style="color:#94a3b8;font-size:12px;white-space:nowrap">{fmt(j["created_at"])}</td>
            </tr>"""
        return rows or '<tr><td colspan="5" class="empty">No job descriptions yet.</td></tr>'

    def users_rows():
        rows = ""
        for u in users:
            color = "#4f46e5" if u["user_type"] == "employer" else "#22c55e"
            rows += f"""<tr>
              <td style="font-family:monospace;color:#64748b;font-size:11px">{u["id"]}</td>
              <td>{badge(u["user_type"], color)}</td>
              <td style="color:#94a3b8;font-size:12px;white-space:nowrap">{fmt(u["created_at"])}</td>
            </tr>"""
        return rows or '<tr><td colspan="3" class="empty">No users yet.</td></tr>'

    generated_at = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sath Bot — Signup Report</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:#0f1117;color:#e2e8f0;font-family:Inter,system-ui,sans-serif;padding:32px 28px}}
  h1{{font-size:22px;font-weight:700;margin-bottom:4px}}
  .sub{{color:#64748b;font-size:13px;margin-bottom:32px}}
  .stats{{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:36px}}
  .stat{{background:#161b27;border:1px solid #1e2535;border-radius:12px;padding:16px 24px;min-width:130px}}
  .stat .num{{font-size:32px;font-weight:700;color:#818cf8}}
  .stat .lbl{{font-size:12px;color:#64748b;margin-top:4px}}
  h2{{font-size:13px;font-weight:600;margin-bottom:12px;color:#64748b;letter-spacing:.06em;text-transform:uppercase}}
  .section{{margin-bottom:40px}}
  table{{width:100%;border-collapse:collapse;background:#161b27;border:1px solid #1e2535;border-radius:10px;overflow:hidden}}
  th{{background:#1e2535;color:#64748b;font-size:11px;font-weight:600;text-align:left;
      padding:10px 16px;letter-spacing:.06em;text-transform:uppercase}}
  td{{padding:11px 16px;border-top:1px solid #1e253566;font-size:13px;vertical-align:middle}}
  tr:hover td{{background:#1a2030}}
  .empty{{color:#334155;font-size:13px}}
</style>
</head>
<body>
<h1>🤖 Sath Bot — Signup Activity</h1>
<p class="sub">Live from Railway DB &nbsp;·&nbsp; {generated_at}</p>

<div class="stats">
  <div class="stat"><div class="num">{len(users)}</div><div class="lbl">Total Sessions</div></div>
  <div class="stat"><div class="num">{len(candidates)}</div><div class="lbl">Candidates</div></div>
  <div class="stat"><div class="num">{len(employers)}</div><div class="lbl">Employers</div></div>
  <div class="stat"><div class="num">{len(jds)}</div><div class="lbl">JDs Posted</div></div>
</div>

<div class="section">
  <h2>Candidates who signed up</h2>
  <table>
    <thead><tr><th>Name</th><th>Profile</th><th>Resume Preview</th><th>Signed Up</th></tr></thead>
    <tbody>{candidates_rows()}</tbody>
  </table>
</div>

<div class="section">
  <h2>Companies / Employers</h2>
  <table>
    <thead><tr><th>Company</th><th>Signed Up</th></tr></thead>
    <tbody>{employers_rows()}</tbody>
  </table>
</div>

<div class="section">
  <h2>Job Descriptions Posted</h2>
  <table>
    <thead><tr><th>Role</th><th>Company</th><th>Status</th><th>JD Preview</th><th>Posted</th></tr></thead>
    <tbody>{jds_rows()}</tbody>
  </table>
</div>

<div class="section">
  <h2>All User Sessions</h2>
  <table>
    <thead><tr><th>Session ID</th><th>Type</th><th>Registered</th></tr></thead>
    <tbody>{users_rows()}</tbody>
  </table>
</div>
</body></html>"""
    return HTMLResponse(content=html)


# Serve built React frontend from web/dist if it exists
_dist = os.path.join(os.path.dirname(__file__), "..", "web", "dist")
if os.path.isdir(_dist):
    app.mount("/", StaticFiles(directory=_dist, html=True), name="frontend")
