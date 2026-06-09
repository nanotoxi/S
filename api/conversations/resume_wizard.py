import json
import logging
import os
import tempfile

logger = logging.getLogger(__name__)


def msg(content: str) -> dict:
    return {"type": "bot_message", "content": content}


def file_request(content: str) -> dict:
    return {"type": "file_request", "content": content}


def done() -> dict:
    return {"type": "done", "content": ""}


class ResumeWizard:
    def start(self, session) -> dict:
        session.state = "AWAIT_RESUME"
        return file_request(
            "Please upload your resume (PDF or DOCX format). 📄\n"
            "I'll parse it and help you fill in any missing details."
        )

    async def handle(self, session, msg_type: str, content: str, upload_id: str = None, **services) -> list:
        llm = services["llm_service"]
        embedder = services["embedder"]
        db = services["db"]
        resume_parser = services["resume_parser"]
        sm = services["session_manager"]
        state = session.state

        if state == "AWAIT_RESUME":
            if msg_type != "file_ready" or not upload_id:
                return [file_request("Please upload your resume as a PDF or DOCX file.")]

            file_bytes, filename = sm.get_upload(upload_id)
            if not file_bytes:
                return [file_request("Upload not found. Please try uploading again.")]

            if not (filename.lower().endswith(".pdf") or filename.lower().endswith(".docx")):
                return [file_request("Please upload a PDF or DOCX file.")]

            suffix = ".pdf" if filename.lower().endswith(".pdf") else ".docx"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name

            responses = [msg("Received! Parsing your resume now... ⏳")]
            try:
                raw_text = resume_parser.extract_text(tmp_path)
                if not raw_text:
                    return [msg("Sorry, couldn't extract text from this file. Please try a different version.")]

                structured_json_str = await llm.parse_resume(raw_text)
                structured_data = json.loads(structured_json_str)
                session.data["temp_resume_data"] = structured_data
                session.data["temp_raw_text"] = raw_text

                gap_json_str = await llm.identify_resume_gaps(structured_data)
                gap_data = json.loads(gap_json_str)
                session.gaps = gap_data.get("gaps", [])
                sm.delete_upload(upload_id)

                if session.gaps:
                    gap = session.gaps.pop(0)
                    session.current_gap = gap
                    session.state = "FILL_GAP"
                    responses.append(
                        msg(
                            f"I've analyzed your resume! To make it stronger, could you tell me:\n\n"
                            f"👉 {gap['question']}"
                        )
                    )
                else:
                    responses += await self._finalize(session, embedder, db)
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

            return responses

        if state == "FILL_GAP":
            answer_lower = content.strip().lower()
            gap = session.current_gap
            field = gap.get("field", "").lower()

            negative = ["no", "none", "don't have", "n/a", "na", "skip", "i don't have", "not available"]
            is_negative = any(n == answer_lower or f" {n} " in f" {answer_lower} " for n in negative)
            final_value = "Not Provided" if is_negative else content

            data = session.data["temp_resume_data"]
            if "linkedin" in field:
                data.setdefault("social", {})["linkedin"] = final_value
            elif "github" in field:
                data.setdefault("social", {})["github"] = final_value
            elif "instagram" in field:
                data.setdefault("social", {})["instagram"] = final_value
            elif "portfolio" in field:
                data.setdefault("social", {})["portfolio"] = final_value
            elif "summary" in field:
                data["summary"] = final_value
            else:
                data.setdefault("enrichment", []).append({"field": field, "answer": final_value})

            if session.gaps:
                next_gap = session.gaps.pop(0)
                session.current_gap = next_gap
                return [msg(next_gap["question"])]
            else:
                return await self._finalize(session, embedder, db)

        return []

    async def _finalize(self, session, embedder, db) -> list:
        raw_text = session.data["temp_raw_text"]
        structured_data = session.data["temp_resume_data"]

        embedding_list = embedder.get_embedding(raw_text)
        embedding_str = str(embedding_list) if embedding_list else None
        web_uid = abs(hash(session.session_id)) % (2 ** 31 - 1)

        await db.execute(
            "INSERT INTO users (id, user_type) VALUES ($1, 'candidate') ON CONFLICT (id) DO NOTHING",
            web_uid,
        )

        await db.execute(
            """INSERT INTO candidates (user_id, resume_raw, resume_structured, embedding, profile_complete)
               VALUES ($1, $2, $3, $4, true)
               ON CONFLICT (user_id) DO UPDATE
               SET resume_raw = $2, resume_structured = $3, embedding = $4, updated_at = now()""",
            web_uid,
            raw_text,
            json.dumps(structured_data),
            embedding_str,
        )

        session.state = "DONE"
        return [
            msg("Done! Your profile is now complete and active. ✨\n\nYou'll be notified when matching jobs are found."),
            done(),
        ]
