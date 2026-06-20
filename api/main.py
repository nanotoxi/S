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

    def chip(text, color="#4f46e5"):
        return (f'<span style="background:{color}18;color:{color};border:1px solid {color}33;'
                f'padding:3px 10px;border-radius:20px;font-size:11px;white-space:nowrap;'
                f'display:inline-block;margin:2px 3px 2px 0">{text}</span>')

    candidates = await db.fetch(
        "SELECT profile_complete, resume_structured, created_at FROM candidates ORDER BY created_at DESC"
    )
    jds = await db.fetch("""
        SELECT j.title, j.status, j.full_jd, j.structured_jd, j.created_at, e.company_name
        FROM job_descriptions j
        LEFT JOIN employers e ON e.id = j.employer_id
        ORDER BY j.created_at DESC
    """)

    # ── Candidate cards ──────────────────────────────────────────────
    def candidate_cards():
        if not candidates:
            return '<p style="color:#334155;padding:24px">No candidates yet.</p>'
        cards = ""
        for c in candidates:
            try:
                rs = c["resume_structured"]
                if isinstance(rs, str):
                    rs = json.loads(rs)
            except Exception:
                rs = {}
            rs = rs or {}
            personal   = rs.get("personal", {})
            name       = personal.get("name", "Unknown")
            email      = personal.get("email", "")
            phone      = personal.get("phone", "")
            location   = personal.get("location", "")
            summary    = rs.get("summary", "") or ""
            skills_obj = rs.get("skills", {})
            tech       = skills_obj.get("technical", []) if isinstance(skills_obj, dict) else []
            soft       = skills_obj.get("soft", []) if isinstance(skills_obj, dict) else []
            education  = rs.get("education", []) or []
            projects   = rs.get("projects", []) or []
            social     = rs.get("social", {}) or {}
            initials   = "".join(w[0] for w in name.split()[:2]).upper() or "?"
            status_col = "#22c55e" if c["profile_complete"] else "#f59e0b"
            status_txt = "Profile Complete" if c["profile_complete"] else "Incomplete"

            # skills chips
            tech_chips = "".join(chip(s, "#6366f1") for s in tech) or '<span style="color:#334155">—</span>'
            soft_chips = "".join(chip(s, "#0ea5e9") for s in soft) if soft else ""

            # education rows
            edu_rows = ""
            for e in education:
                edu_rows += f"""<div style="margin-bottom:6px">
                  <span style="font-weight:500;color:#e2e8f0">{e.get('degree','')}</span>
                  <span style="color:#64748b"> · {e.get('institution','')} · {e.get('year','')}
                  {(' · ' + e.get('grade','')) if e.get('grade') else ''}</span>
                </div>"""

            # project rows
            proj_rows = ""
            for p in projects[:4]:
                t = "".join(chip(x, "#7c3aed") for x in (p.get("tech_stack") or []))
                proj_rows += f"""<div style="margin-bottom:10px">
                  <span style="font-weight:600;color:#e2e8f0">{p.get('name','')}</span>
                  <span style="color:#64748b;font-size:12px"> — {p.get('description','')}</span>
                  <div style="margin-top:4px">{t}</div>
                </div>"""

            # social links
            socials = ""
            for key, label, color in [("linkedin","LinkedIn","#0a66c2"),("github","GitHub","#e2e8f0"),("portfolio","Portfolio","#4f46e5")]:
                val = social.get(key, "")
                if val and val.lower() not in ("not provided", ""):
                    socials += f'<a href="{val}" target="_blank" style="color:{color};font-size:12px;margin-right:12px;text-decoration:none">🔗 {label}</a>'

            summary_html = f'<p style="color:#94a3b8;font-size:13px;line-height:1.6;margin-bottom:16px">{summary}</p>' if summary and summary.lower() != "not provided" else ""

            cards += f"""
<div style="background:#161b27;border:1px solid #1e2535;border-radius:16px;padding:24px;margin-bottom:20px">
  <div style="display:flex;align-items:flex-start;gap:16px;margin-bottom:18px">
    <div style="width:52px;height:52px;border-radius:50%;background:#4f46e5;display:flex;
        align-items:center;justify-content:center;font-size:18px;font-weight:700;
        color:#fff;flex-shrink:0">{initials}</div>
    <div style="flex:1">
      <div style="font-size:18px;font-weight:700;color:#e2e8f0">{name}</div>
      <div style="color:#64748b;font-size:13px;margin-top:3px">
        {('📧 ' + email + ' &nbsp;') if email else ''}
        {('📱 ' + phone + ' &nbsp;') if phone else ''}
        {('📍 ' + location) if location else ''}
      </div>
      {socials}
    </div>
    <div style="text-align:right;flex-shrink:0">
      <span style="background:{status_col}18;color:{status_col};border:1px solid {status_col}33;
          padding:3px 10px;border-radius:20px;font-size:11px">{status_txt}</span>
      <div style="color:#64748b;font-size:11px;margin-top:6px">{fmt(c['created_at'])}</div>
    </div>
  </div>

  {summary_html}

  <div style="margin-bottom:16px">
    <div style="font-size:11px;font-weight:600;color:#64748b;letter-spacing:.06em;
        text-transform:uppercase;margin-bottom:8px">Technical Skills</div>
    <div>{tech_chips}</div>
    {('<div style="margin-top:6px">' + soft_chips + '</div>') if soft_chips else ''}
  </div>

  {('<div style="margin-bottom:16px"><div style="font-size:11px;font-weight:600;color:#64748b;letter-spacing:.06em;text-transform:uppercase;margin-bottom:8px">Education</div>' + edu_rows + '</div>') if edu_rows else ''}

  {('<div><div style="font-size:11px;font-weight:600;color:#64748b;letter-spacing:.06em;text-transform:uppercase;margin-bottom:8px">Projects</div>' + proj_rows + '</div>') if proj_rows else ''}
</div>"""
        return cards

    # ── JD cards ─────────────────────────────────────────────────────
    def jd_cards():
        if not jds:
            return '<p style="color:#334155;padding:24px">No job descriptions yet.</p>'
        cards = ""
        for j in jds:
            try:
                sj = j["structured_jd"]
                if isinstance(sj, str):
                    sj = json.loads(sj)
            except Exception:
                sj = {}
            sj = sj or {}
            title       = j["title"] or sj.get("title", "Untitled")
            company     = j["company_name"] or sj.get("company_name", "—")
            emp_type    = sj.get("employment_type", "")
            location    = sj.get("location", "")
            experience  = sj.get("experience", "")
            skills      = sj.get("skills", []) or []
            resp        = sj.get("responsibilities", []) or []
            full_jd     = (j["full_jd"] or "").replace("<", "&lt;").replace(">", "&gt;")

            skill_chips = "".join(chip(s, "#6366f1") for s in skills)
            resp_items  = "".join(f'<li style="color:#94a3b8;font-size:13px;margin-bottom:4px">{r}</li>' for r in resp)
            meta_parts  = " &nbsp;·&nbsp; ".join(x for x in [emp_type, location, experience] if x)

            cards += f"""
<div style="background:#161b27;border:1px solid #1e2535;border-radius:16px;padding:24px;margin-bottom:20px">
  <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:16px;margin-bottom:16px">
    <div>
      <div style="font-size:18px;font-weight:700;color:#e2e8f0">{title}</div>
      <div style="color:#818cf8;font-size:14px;font-weight:500;margin-top:4px">{company}</div>
      <div style="color:#64748b;font-size:12px;margin-top:4px">{meta_parts}</div>
    </div>
    <div style="text-align:right;flex-shrink:0">
      <span style="background:#22c55e18;color:#22c55e;border:1px solid #22c55e33;
          padding:3px 10px;border-radius:20px;font-size:11px">{j['status']}</span>
      <div style="color:#64748b;font-size:11px;margin-top:6px">{fmt(j['created_at'])}</div>
    </div>
  </div>

  {('<div style="margin-bottom:14px"><div style="font-size:11px;font-weight:600;color:#64748b;letter-spacing:.06em;text-transform:uppercase;margin-bottom:8px">Skills Required</div><div>' + skill_chips + '</div></div>') if skill_chips else ''}

  {('<div style="margin-bottom:14px"><div style="font-size:11px;font-weight:600;color:#64748b;letter-spacing:.06em;text-transform:uppercase;margin-bottom:8px">Responsibilities</div><ul style="padding-left:18px">' + resp_items + '</ul></div>') if resp_items else ''}

  <details style="margin-top:8px">
    <summary style="color:#4f46e5;font-size:12px;cursor:pointer;list-style:none">▶ View full JD</summary>
    <pre style="margin-top:12px;background:#0f1117;border:1px solid #1e2535;border-radius:8px;
        padding:14px;font-size:12px;color:#94a3b8;white-space:pre-wrap;
        font-family:inherit;line-height:1.6">{full_jd}</pre>
  </details>
</div>"""
        return cards

    generated_at = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sath Bot — Signups</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:#0f1117;color:#e2e8f0;font-family:Inter,system-ui,sans-serif;padding:32px 28px;max-width:900px;margin:0 auto}}
  h1{{font-size:22px;font-weight:700;margin-bottom:4px}}
  .sub{{color:#64748b;font-size:13px;margin-bottom:32px}}
  .stats{{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:36px}}
  .stat{{background:#161b27;border:1px solid #1e2535;border-radius:12px;padding:16px 24px;min-width:130px}}
  .stat .num{{font-size:32px;font-weight:700;color:#818cf8}}
  .stat .lbl{{font-size:12px;color:#64748b;margin-top:4px}}
  h2{{font-size:13px;font-weight:600;margin-bottom:16px;color:#64748b;letter-spacing:.06em;text-transform:uppercase}}
  .section{{margin-bottom:48px}}
  details summary::-webkit-details-marker{{display:none}}
</style>
</head>
<body>
<h1>🤖 Sath Bot — Signup Activity</h1>
<p class="sub">Live · Railway DB · {generated_at}</p>

<div class="stats">
  <div class="stat"><div class="num">{len(candidates)}</div><div class="lbl">Candidates</div></div>
  <div class="stat"><div class="num">{len(jds)}</div><div class="lbl">Job Postings</div></div>
</div>

<div class="section">
  <h2>Candidates</h2>
  {candidate_cards()}
</div>

<div class="section">
  <h2>Job Descriptions Posted</h2>
  {jd_cards()}
</div>
</body></html>"""
    return HTMLResponse(content=html)


# Serve built React frontend from web/dist if it exists
_dist = os.path.join(os.path.dirname(__file__), "..", "web", "dist")
if os.path.isdir(_dist):
    app.mount("/", StaticFiles(directory=_dist, html=True), name="frontend")
