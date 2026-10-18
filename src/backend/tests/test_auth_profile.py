from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

import jwt
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.security import create_access_token
from app.infrastructure.persistence.database import get_db_session
from app.main import app


def test_protected_routes_reject_missing_and_expired_tokens():
    db = MagicMock()
    app.dependency_overrides[get_db_session] = lambda: db
    try:
        client = TestClient(app)
        for path in ("/api/auth/me", "/api/applicants/me"):
            assert client.get(path).status_code == 401
        token = jwt.encode(
            {
                "sub": str(uuid4()),
                "iat": datetime.now(UTC) - timedelta(hours=2),
                "exp": datetime.now(UTC) - timedelta(hours=1),
                "type": "access",
            },
            get_settings().jwt_secret,
            algorithm="HS256",
        )
        assert (
            client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code
            == 401
        )
        db.execute.assert_not_called()
    finally:
        app.dependency_overrides.clear()


def test_me_returns_user_without_password_and_rejects_recruiter_profile_access():
    user_id = uuid4()
    db = MagicMock()
    db.execute.return_value.mappings.return_value.one_or_none.return_value = {
        "id": user_id,
        "email": "recruiter@example.com",
        "full_name": "Recruiter",
        "role": "RECRUITER",
        "status": "ACTIVE",
        "password_hash": "must-not-be-returned",
    }
    app.dependency_overrides[get_db_session] = lambda: db
    try:
        client = TestClient(app)
        headers = {"Authorization": f"Bearer {create_access_token(user_id, uuid4())}"}
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 200
        assert response.json()["id"] == str(user_id)
        assert "password_hash" not in response.json()
        assert client.get("/api/applicants/me", headers=headers).status_code == 403
    finally:
        app.dependency_overrides.clear()
