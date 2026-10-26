"""Provider mocked tests do not call paid/external services."""

import json

import httpx
from fastapi.testclient import TestClient

from app.api.routes.completion import ExplanationText
from app.core.config import get_settings
from app.infrastructure.ai.assistant import generate_json
from app.main import app


def test_ai_timeout_and_output_validation(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "ai_provider", "gemini")
    monkeypatch.setattr(settings, "ai_api_key", "test-key")
    monkeypatch.setattr(settings, "ai_model", "test-model")
    original = httpx.Client
    seen = []

    def handler(request):
        seen.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {"content": {"parts": [{"text": '{"explanation":"Based on shared skills."}'}]}}
                ]
            },
        )

    monkeypatch.setattr(
        httpx, "Client", lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs)
    )
    output, reason = generate_json("Explain", {"matched_skills": ["Python"]}, ExplanationText)
    assert output.explanation and reason is None
    assert "password" not in json.dumps(seen) and "user_id" not in json.dumps(seen)

    def timeout(request):
        raise httpx.ReadTimeout("test", request=request)

    monkeypatch.setattr(
        httpx, "Client", lambda **kwargs: original(transport=httpx.MockTransport(timeout), **kwargs)
    )
    output, reason = generate_json("Explain", {}, ExplanationText)
    assert output is None and reason
    monkeypatch.setattr(
        httpx,
        "Client",
        lambda **kwargs: original(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json={"candidates": []})
            ),
            **kwargs,
        ),
    )
    assert generate_json("Explain", {}, ExplanationText)[0] is None


def test_host_headers_and_auth_rate_limit(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "auth_rate_limit_per_minute", 1)
    # Fresh app avoids rate-limit buckets from other tests.
    from fastapi import FastAPI

    from app.api.middleware.security import RequestSecurityMiddleware

    limited = FastAPI()
    limited.add_middleware(RequestSecurityMiddleware)

    @limited.post("/api/auth/login")
    def login():
        return {"ok": True}

    with TestClient(limited) as client:
        assert client.post("/api/auth/login").status_code == 200
        response = client.post("/api/auth/login")
        assert response.status_code == 429 and response.headers["retry-after"] == "60"
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.headers["x-content-type-options"] == "nosniff"
        assert client.get("/api/health", headers={"host": "malicious.example"}).status_code == 400
