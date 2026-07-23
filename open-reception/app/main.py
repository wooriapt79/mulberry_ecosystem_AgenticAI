from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


def now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String, default="member")
    disabled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class LoginSession(Base):
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)


class HumanPassport(Base):
    __tablename__ = "human_passports"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True)
    display_name: Mapped[str] = mapped_column(String)
    domains: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String, default="active")
    policy_version: Mapped[str] = mapped_column(String, default="2026-07")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class StewardApplication(Base):
    __tablename__ = "steward_human_applications"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    domain: Mapped[str] = mapped_column(String)
    statement: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="pending")
    reviewed_by: Mapped[str | None] = mapped_column(String, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AiPassport(Base):
    __tablename__ = "ai_passports"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    level: Mapped[str] = mapped_column(String)
    domains: Mapped[list] = mapped_column(JSON)
    permissions: Mapped[list] = mapped_column(JSON)
    spirit_score: Mapped[float] = mapped_column(Float)
    mentor_agent: Mapped[str | None] = mapped_column(String, nullable=True)
    origin_agent: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="active")


class MatchRequest(Base):
    __tablename__ = "matching_requests"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    requester_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    domain: Mapped[str] = mapped_column(String)
    risk: Mapped[str] = mapped_column(String)
    required_permissions: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String, default="recommendation_only")
    approved_by: Mapped[str | None] = mapped_column(String, nullable=True)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    actor_id: Mapped[str] = mapped_column(String)
    action: Mapped[str] = mapped_column(String)
    target_type: Mapped[str] = mapped_column(String)
    target_id: Mapped[str] = mapped_column(String)
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class KillSwitch(Base):
    __tablename__ = "kill_switches"
    id: Mapped[str] = mapped_column(String, primary_key=True, default="global")
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    reason: Mapped[str] = mapped_column(String, default="")
    changed_by: Mapped[str] = mapped_column(String, default="system")
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./open_reception.sqlite3")
engine_args = {"connect_args": {"check_same_thread": False}} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, **engine_args)
SessionLocal = sessionmaker(engine, expire_on_commit=False)

app = FastAPI(title="Luna Open Reception", version="0.1.0")


def db_session():
    with SessionLocal() as db:
        yield db


def password_hash(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return f"pbkdf2_sha256$310000${salt.hex()}${digest.hex()}"


def password_valid(password: str, encoded: str) -> bool:
    _, rounds, salt, expected = encoded.split("$")
    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(rounds))
    return hmac.compare_digest(actual.hex(), expected)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def audit(db: Session, actor: str, action: str, target_type: str, target_id: str, detail: dict | None = None):
    db.add(AuditEvent(actor_id=actor, action=action, target_type=target_type, target_id=target_id, detail=detail or {}))


def current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: Session = Depends(db_session),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Bearer token required")
    session = db.scalar(select(LoginSession).where(LoginSession.token_hash == token_hash(authorization[7:])))
    if not session or session.revoked or session.expires_at.replace(tzinfo=timezone.utc) <= now():
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired session")
    user = db.get(User, session.user_id)
    if not user or user.disabled:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account disabled")
    return user


def require_admin(user: User = Depends(current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Human administrator approval required")
    return user


def enforce_kill_switch(db: Session):
    switch = db.get(KillSwitch, "global")
    if switch and switch.active:
        raise HTTPException(status.HTTP_423_LOCKED, f"Delegation disabled: {switch.reason}")


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=256)


class PassportInput(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    domains: list[str] = Field(default_factory=list, max_length=20)


class ApplicationInput(BaseModel):
    domain: str = Field(min_length=2, max_length=80)
    statement: str = Field(min_length=20, max_length=2000)


class ReviewInput(BaseModel):
    approved: bool


class MatchInput(BaseModel):
    domain: str
    risk: Literal["low", "medium", "high"] = "low"
    required_permissions: list[str] = Field(default_factory=list)


class KillInput(BaseModel):
    active: bool
    reason: str = Field(min_length=3, max_length=500)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if not db.get(KillSwitch, "global"):
            db.add(KillSwitch())
        if not db.get(AiPassport, "luna"):
            db.add(AiPassport(
                id="luna", name="Luna", level="professional",
                domains=["reception", "food-desert", "membership-guidance"],
                permissions=["research", "recommend", "draft"],
                spirit_score=0.90, origin_agent="jr-trang", mentor_agent="nguyen-trang",
            ))
        if not db.get(AiPassport, "jr-trang"):
            db.add(AiPassport(
                id="jr-trang", name="Jr. TRANG", level="junior",
                domains=["research", "food-desert"], permissions=["research", "draft"],
                spirit_score=0.76, mentor_agent="luna",
            ))
        db.commit()


@app.get("/health")
def health():
    return {"status": "ok", "dry_run": True}


@app.post("/auth/register", status_code=201)
def register(payload: Credentials, db: Session = Depends(db_session)):
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    user = User(email=email, password_hash=password_hash(payload.password))
    db.add(user)
    db.flush()
    audit(db, user.id, "user.registered", "user", user.id)
    db.commit()
    return {"id": user.id, "status": "member"}


@app.post("/auth/login")
def login(payload: Credentials, db: Session = Depends(db_session)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not password_valid(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    token = secrets.token_urlsafe(32)
    ttl = int(os.getenv("SESSION_TTL_MINUTES", "60"))
    login_session = LoginSession(user_id=user.id, token_hash=token_hash(token), expires_at=now() + timedelta(minutes=ttl))
    db.add(login_session)
    db.flush()
    audit(db, user.id, "session.created", "session", login_session.id)
    db.commit()
    return {"access_token": token, "token_type": "bearer", "expires_in": ttl * 60}


@app.put("/passport/human")
def upsert_passport(payload: PassportInput, user: User = Depends(current_user), db: Session = Depends(db_session)):
    passport = db.scalar(select(HumanPassport).where(HumanPassport.user_id == user.id))
    if passport:
        passport.display_name, passport.domains = payload.display_name, payload.domains
    else:
        passport = HumanPassport(user_id=user.id, display_name=payload.display_name, domains=payload.domains)
        db.add(passport)
    db.flush()
    audit(db, user.id, "human_passport.upserted", "human_passport", passport.id)
    db.commit()
    return {"id": passport.id, "status": passport.status, "policy_version": passport.policy_version}


@app.post("/steward-human/applications", status_code=201)
def apply_steward(payload: ApplicationInput, user: User = Depends(current_user), db: Session = Depends(db_session)):
    passport = db.scalar(select(HumanPassport).where(HumanPassport.user_id == user.id, HumanPassport.status == "active"))
    if not passport:
        raise HTTPException(status.HTTP_409_CONFLICT, "Active Human Passport required")
    application = StewardApplication(user_id=user.id, domain=payload.domain, statement=payload.statement)
    db.add(application)
    db.flush()
    audit(db, user.id, "steward_application.submitted", "steward_application", application.id)
    db.commit()
    return {"id": application.id, "status": application.status}


@app.post("/admin/steward-human/applications/{application_id}/review")
def review_steward(application_id: str, payload: ReviewInput, admin: User = Depends(require_admin), db: Session = Depends(db_session)):
    application = db.get(StewardApplication, application_id)
    if not application or application.status != "pending":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pending application not found")
    application.status = "approved" if payload.approved else "rejected"
    application.reviewed_by, application.reviewed_at = admin.id, now()
    if payload.approved:
        applicant = db.get(User, application.user_id)
        applicant.role = "steward_human"
    audit(db, admin.id, f"steward_application.{application.status}", "steward_application", application.id)
    db.commit()
    return {"id": application.id, "status": application.status}


@app.post("/matching/recommendations")
def recommend(payload: MatchInput, user: User = Depends(current_user), db: Session = Depends(db_session)):
    enforce_kill_switch(db)
    request = MatchRequest(
        requester_id=user.id, domain=payload.domain, risk=payload.risk,
        required_permissions=payload.required_permissions,
    )
    db.add(request)
    candidates = []
    for agent in db.scalars(select(AiPassport).where(AiPassport.status == "active")).all():
        if agent.spirit_score < 0.4 or payload.domain not in agent.domains:
            continue
        permission_fit = len(set(payload.required_permissions) & set(agent.permissions)) / max(len(payload.required_permissions), 1)
        domain_fit = 1.0
        safety = 1.0 if payload.risk == "low" else (0.7 if agent.level != "junior" else 0.3)
        score = round(0.30 * domain_fit + 0.20 * (0.8 if agent.level != "junior" else 0.4) + 0.20 * safety + 0.15 * permission_fit + 0.10 * agent.spirit_score + 0.05, 3)
        candidates.append({
            "agent_id": agent.id, "name": agent.name, "level": agent.level, "score": score,
            "requires_supervision": agent.level == "junior",
            "allowed_actions": agent.permissions,
            "explanation": f"domain={payload.domain}; spirit={agent.spirit_score}; risk={payload.risk}",
        })
    candidates.sort(key=lambda item: item["score"], reverse=True)
    audit(db, user.id, "matching.recommended", "matching_request", request.id, {"candidate_ids": [c["agent_id"] for c in candidates[:3]]})
    db.commit()
    return {"request_id": request.id, "status": "recommendation_only", "human_approval_required": True, "candidates": candidates[:3]}


@app.post("/admin/kill-switch")
def set_kill_switch(payload: KillInput, admin: User = Depends(require_admin), db: Session = Depends(db_session)):
    switch = db.get(KillSwitch, "global")
    switch.active, switch.reason, switch.changed_by, switch.changed_at = payload.active, payload.reason, admin.id, now()
    audit(db, admin.id, "kill_switch.changed", "kill_switch", "global", {"active": payload.active, "reason": payload.reason})
    db.commit()
    return {"active": switch.active, "reason": switch.reason}
