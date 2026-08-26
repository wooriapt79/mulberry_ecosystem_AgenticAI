from __future__ import annotations

import os
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.services.demo_service import contains_pii, generate_demo_reply

router = APIRouter(prefix="/demo", tags=["demo"])

# In-memory sliding-window rate limiter: 10 req/min per IP
_rate_lock = Lock()
_rate_buckets: dict[str, deque] = defaultdict(deque)
_RATE_LIMIT = 10
_RATE_WINDOW = 60.0


def _check_rate_limit(ip: str) -> None:
    now = time.monotonic()
    with _rate_lock:
        bucket = _rate_buckets[ip]
        while bucket and now - bucket[0] > _RATE_WINDOW:
            bucket.popleft()
        if len(bucket) >= _RATE_LIMIT:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                "데모 요청 한도 초과입니다. 잠시 후 다시 시도해 주세요.",
            )
        bucket.append(now)


class DemoChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)


class DemoChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=DemoChatResponse)
def demo_chat(payload: DemoChatRequest, request: Request) -> DemoChatResponse:
    if not os.getenv("DEMO_MODE", "").lower() in {"1", "true", "yes"}:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(client_ip)

    if contains_pii(payload.message):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "개인정보(전화번호, 이메일, 주민등록번호 등)는 입력하지 마세요.",
        )

    reply = generate_demo_reply(payload.message)
    return DemoChatResponse(reply=reply)
