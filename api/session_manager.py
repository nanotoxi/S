import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Session:
    session_id: str
    role: Optional[str] = None  # 'employer' | 'candidate'
    state: str = 'ROLE_SELECT'
    data: dict = field(default_factory=dict)
    gaps: list = field(default_factory=list)
    current_gap: Optional[dict] = None


class SessionManager:
    def __init__(self):
        self._sessions: dict[str, Session] = {}
        self._uploads: dict[str, bytes] = {}
        self._upload_names: dict[str, str] = {}

    def create_session(self) -> Session:
        session_id = str(uuid.uuid4())
        session = Session(session_id=session_id)
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)

    def store_upload(self, file_bytes: bytes, filename: str) -> str:
        upload_id = str(uuid.uuid4())
        self._uploads[upload_id] = file_bytes
        self._upload_names[upload_id] = filename
        return upload_id

    def get_upload(self, upload_id: str):
        return self._uploads.get(upload_id), self._upload_names.get(upload_id)

    def delete_upload(self, upload_id: str):
        self._uploads.pop(upload_id, None)
        self._upload_names.pop(upload_id, None)


session_manager = SessionManager()
