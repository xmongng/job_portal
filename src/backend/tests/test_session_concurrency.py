"""Real separate connections verify one-time refresh rotation under concurrent requests."""

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.application.auth.sessions import rotate_session
from app.core.security import create_refresh_token, hash_refresh_token
from app.infrastructure.persistence import stores


def test_refresh_token_can_only_rotate_once(integration_engine):
    user_id = None
    token = create_refresh_token()
    try:
        with Session(integration_engine) as db:
            user = stores.one(
                db,
                "register_user",
                email=f"race-{uuid4().hex}@example.com",
                password_hash="!test-only!",
                full_name="Race test",
                role="APPLICANT",
            )
            user_id = user.id
            stores.execute(
                db,
                "create_auth_session",
                user_id=user_id,
                refresh_token_hash=hash_refresh_token(token),
                expires_at=datetime.now(UTC) + timedelta(days=1),
            )
            db.commit()

        def rotate():
            with Session(integration_engine) as db:
                try:
                    rotate_session(db, token, create_refresh_token())
                    db.commit()
                    return 200
                except HTTPException as exc:
                    db.rollback()
                    return exc.status_code

        with ThreadPoolExecutor(max_workers=2) as pool:
            assert sorted(pool.map(lambda _: rotate(), range(2))) == [200, 401]
    finally:
        if user_id:
            # Test teardown only; application code always uses stores.
            with integration_engine.begin() as conn:
                conn.execute(text("DELETE FROM auth_sessions WHERE user_id=:id"), {"id": user_id})
                conn.execute(text("DELETE FROM users WHERE id=:id"), {"id": user_id})
