"""레이트리밋 전용 테스트.

conftest.py 가 TESTING=true 로 설정하므로 일반 회귀 테스트에서는 limiter 가 꺼진다.
이 모듈의 각 테스트는 rate_limit_active fixture 로 limiter 를 켜고
테스트 종료 후 되돌린다.

NOTE: TestClient.request.client.host 는 항상 "testclient" 이므로
      IP 분리 테스트(KeBin §5-6)는 X-Forwarded-For 신뢰 설정 구현 후 추가한다.
"""
import io
import os

import pytest
from fastapi.testclient import TestClient

from app.main import _analyze_file_limiter, limiter


@pytest.fixture()
def rate_limit_active():
    """각 테스트 전후 limiter 활성화 + 저장소 초기화."""
    prev_testing = os.environ.get("TESTING", "true")
    os.environ["TESTING"] = "false"
    limiter.enabled = True
    try:
        limiter._limiter.storage.storage.clear()
    except Exception:
        pass
    _analyze_file_limiter._buckets.clear()
    yield
    _analyze_file_limiter._buckets.clear()
    try:
        limiter._limiter.storage.storage.clear()
    except Exception:
        pass
    limiter.enabled = False
    os.environ["TESTING"] = prev_testing


@pytest.fixture()
def client(rate_limit_active):
    from app.main import app as _app
    return TestClient(_app)


def test_bootstrap_rate_limit_429(client):
    for _ in range(3):
        client.post("/auth/bootstrap", json={"bootstrap_token": "wrong", "email": "a@b.com", "password": "x"})
    resp = client.post("/auth/bootstrap", json={"bootstrap_token": "wrong", "email": "a@b.com", "password": "x"})
    assert resp.status_code == 429


def test_register_rate_limit_429(client):
    for i in range(3):
        client.post("/auth/register", json={"email": f"rl{i}@example.com", "password": "correct-horse-battery"})
    resp = client.post("/auth/register", json={"email": "rl_over@example.com", "password": "correct-horse-battery"})
    assert resp.status_code == 429


def test_login_rate_limit_429(client):
    for _ in range(5):
        client.post("/auth/login", json={"email": "no@no.com", "password": "wrong"})
    resp = client.post("/auth/login", json={"email": "no@no.com", "password": "wrong"})
    assert resp.status_code == 429


def test_429_no_sensitive_info(client):
    """429 응답에 내부 정보·공급자명이 노출되지 않는다."""
    for _ in range(3):
        client.post("/auth/register", json={"email": "info@example.com", "password": "pw"})
    resp = client.post("/auth/register", json={"email": "info@example.com", "password": "pw"})
    assert resp.status_code == 429
    body = resp.text.lower()
    for forbidden in ("traceback", "anthropic", "railway", "sqlalchemy", "secret"):
        assert forbidden not in body, f"민감 정보 '{forbidden}' 노출됨"


def test_analyze_file_rate_limit_429(client):
    """/api/analyze-file 전용 limiter: 10 회 초과 시 429."""
    dummy = io.BytesIO(b"hello world")
    for _ in range(10):
        dummy.seek(0)
        client.post(
            "/api/analyze-file",
            files={"file": ("t.txt", dummy, "text/plain")},
            data={"page": "inje"},
        )
    dummy.seek(0)
    resp = client.post(
        "/api/analyze-file",
        files={"file": ("t.txt", dummy, "text/plain")},
        data={"page": "inje"},
    )
    assert resp.status_code == 429
