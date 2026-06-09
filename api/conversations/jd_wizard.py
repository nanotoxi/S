import json
import logging

logger = logging.getLogger(__name__)

EMPLOYMENT_OPTIONS = [
    {"label": "Full-time", "value": "Full-time"},
    {"label": "Part-time", "value": "Part-time"},
    {"label": "Contract", "value": "Contract"},
    {"label": "Internship", "value": "Internship"},
]

EXPERIENCE_OPTIONS = [
    {"label": "Fresher (0–1 yr)", "value": "0-1 years"},
    {"label": "1–3 years", "value": "1-3 years"},
    {"label": "3–5 years", "value": "3-5 years"},
    {"label": "5–10 years", "value": "5-10 years"},
    {"label": "10+ years", "value": "10+ years"},
]


def msg(content: str) -> dict:
    return {"type": "bot_message", "content": content}


def options(content: str, choices: list) -> dict:
    return {"type": "options", "content": content, "choices": choices}


def multi_select(content: str, field: str, suggestions: list) -> dict:
    return {"type": "multi_select", "content": content, "field": field, "suggestions": suggestions}


def done() -> dict:
    return {"type": "done", "content": ""}


def _web_user_int(session_id: str) -> int:
    """Stable positive integer derived from session UUID for use as DB user_id."""
    return abs(hash(session_id)) % (2 ** 31 - 1)


class JDWizard:
    def start(self, session) -> dict:
        session.state = "COMPANY_NAME"
        session.data["jd_data"] = {}
        return msg("Let's create a Job Description! 📝\n\nWhat is the **Company Name**?")

    async def handle(self, session, msg_type: str, content: str, **services) -> list:
        state = session.state
        llm = services["llm_service"]
        db = services["db"]
        embedder = services["embedder"]
        rag_engine = services["rag_engine"]
        notifier = services.get("notifier")

        if state == "COMPANY_NAME":
            session.data["jd_data"]["company_name"] = content
            session.state = "ROLE_TITLE"
            return [msg("Got it. What is the **Job Title** or Role?")]

        if state == "ROLE_TITLE":
            session.data["jd_data"]["title"] = content
            session.state = "EMPLOYMENT_TYPE"
            return [options("What is the **Employment Type**?", EMPLOYMENT_OPTIONS)]

        if state == "EMPLOYMENT_TYPE":
            session.data["jd_data"]["employment_type"] = content
            session.state = "LOCATION"
            return [msg(f"Selected: **{content}**.\n\nWhat is the **Location**? (e.g. Remote, Hybrid, Mumbai)")]

        if state == "LOCATION":
            session.data["jd_data"]["location"] = content
            session.state = "EXPERIENCE"
            return [options("How many **years of experience** are required?", EXPERIENCE_OPTIONS)]

        if state == "EXPERIENCE":
            session.data["jd_data"]["experience"] = content
            session.state = "RESPONSIBILITIES"
            suggestions = await llm.suggest_jd_fields(session.data["jd_data"], "responsibilities")
            return [
                msg("Generating responsibility suggestions... ⏳"),
                multi_select(
                    "Select the key **Responsibilities** for this role.\nPick from suggestions or add your own:",
                    "responsibilities",
                    suggestions,
                ),
            ]

        if state == "RESPONSIBILITIES":
            items = json.loads(content) if content.startswith("[") else [s.strip() for s in content.split("\n") if s.strip()]
            session.data["jd_data"]["responsibilities"] = items
            session.state = "SKILLS"
            suggestions = await llm.suggest_jd_fields(session.data["jd_data"], "skills")
            return [
                msg("Generating skill suggestions... ⏳"),
                multi_select(
                    "Select the **Must-have Skills** for this role.\nPick from suggestions or add your own:",
                    "skills",
                    suggestions,
                ),
            ]

        if state == "SKILLS":
            items = json.loads(content) if content.startswith("[") else [s.strip() for s in content.split("\n") if s.strip()]
            session.data["jd_data"]["skills"] = items
            session.state = "GENERATING"
            full_jd = await llm.generate_jd(session.data["jd_data"])
            session.data["full_jd"] = full_jd
            session.state = "CONFIRM_JD"
            return [
                msg("Generating your professional JD... ⏳"),
                options(
                    f"**Draft Job Description:**\n\n{full_jd}",
                    [
                        {"label": "Approve ✅", "value": "approve_jd"},
                        {"label": "Cancel ❌", "value": "cancel_jd"},
                    ],
                ),
            ]

        if state == "CONFIRM_JD":
            if content == "approve_jd":
                responses = [msg("Saving your JD and notifying matching candidates... ⏳")]
                try:
                    embedding_list = embedder.get_embedding(session.data["full_jd"])
                    embedding_str = str(embedding_list) if embedding_list else None
                    web_uid = _web_user_int(session.session_id)

                    # Ensure users row exists (web sessions use synthetic numeric id)
                    await db.execute(
                        "INSERT INTO users (id, user_type) VALUES ($1, 'employer') ON CONFLICT (id) DO NOTHING",
                        web_uid,
                    )

                    employer_row = await db.fetchrow(
                        "SELECT id FROM employers WHERE user_id = $1", web_uid
                    )
                    if not employer_row:
                        employer_id = await db.fetchval(
                            "INSERT INTO employers (user_id, company_name) VALUES ($1, $2) RETURNING id",
                            web_uid, session.data["jd_data"]["company_name"],
                        )
                    else:
                        employer_id = employer_row["id"]

                    jd_id = await db.fetchval(
                        """INSERT INTO job_descriptions
                           (employer_id, title, full_jd, structured_jd, embedding, status)
                           VALUES ($1, $2, $3, $4, $5, 'active') RETURNING id""",
                        employer_id,
                        session.data["jd_data"]["title"],
                        session.data["full_jd"],
                        json.dumps(session.data["jd_data"]),
                        embedding_str,
                    )

                    matches = await rag_engine.find_matching_candidates(embedding_str, limit=10)
                    if matches and notifier:
                        await notifier.notify_candidates_of_new_jd(
                            jd_id, session.data["jd_data"]["title"], matches
                        )

                    responses.append(msg("Your JD is now live! 🚀 Matching candidates have been notified."))
                except Exception as e:
                    logger.error(f"JD save error: {e}", exc_info=True)
                    responses.append(msg(f"⚠️ Error saving JD: {e}"))

                session.state = "DONE"
                responses.append(done())
                return responses
            else:
                session.state = "DONE"
                return [msg("JD generation cancelled."), done()]

        return []
