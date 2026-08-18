from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, case, create_engine, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.matching_policy import (
    DOMAIN_PACK_VERSION,
    MATCHING_POLICY_VERSION,
    evaluate_candidate,
    get_domain_pack,
)


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
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class BootstrapConsumption(Base):
    __tablename__ = "bootstrap_consumptions"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    consumed_by: Mapped[str] = mapped_column(String)
    consumed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class LoginSession(Base):
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_by: Mapped[str | None] = mapped_column(String, nullable=True)
    revoke_reason: Mapped[str | None] = mapped_column(String, nullable=True)


class HumanPassport(Base):
    __tablename__ = "human_passports"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True)
    display_name: Mapped[str] = mapped_column(String)
    domains: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String, default="active")
    policy_version: Mapped[str] = mapped_column(String, default="2026-07")
    status_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    status_changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class HumanPassportStatusHistory(Base):
    __tablename__ = "human_passport_status_history"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    passport_id: Mapped[str] = mapped_column(ForeignKey("human_passports.id"), index=True)
    from_status: Mapped[str | None] = mapped_column(String, nullable=True)
    to_status: Mapped[str] = mapped_column(String)
    reason: Mapped[str] = mapped_column(String)
    changed_by: Mapped[str] = mapped_column(String)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


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


class MatchingRecommendation(Base):
    __tablename__ = "matching_recommendations"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    request_id: Mapped[str] = mapped_column(
        ForeignKey("matching_requests.id"), unique=True, index=True
    )
    domain_pack_version: Mapped[str] = mapped_column(String)
    policy_version: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="recommended")
    rationale: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class MatchingCandidate(Base):
    __tablename__ = "matching_candidates"
    __table_args__ = (
        UniqueConstraint(
            "recommendation_id",
            "agent_passport_id",
            name="uq_matching_candidate_recommendation_agent",
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    recommendation_id: Mapped[str] = mapped_column(
        ForeignKey("matching_recommendations.id"), index=True
    )
    agent_passport_id: Mapped[str] = mapped_column(ForeignKey("ai_passports.id"))
    agent_kind: Mapped[str] = mapped_column(String)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    eligible: Mapped[bool] = mapped_column(Boolean)
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    exclusion_reasons: Mapped[list] = mapped_column(JSON, default=list)
    supervisor_agent_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class MatchingDecision(Base):
    __tablename__ = "matching_decisions"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    recommendation_id: Mapped[str] = mapped_column(
        ForeignKey("matching_recommendations.id"), index=True
    )
    action: Mapped[str] = mapped_column(String)
    from_status: Mapped[str] = mapped_column(String)
    to_status: Mapped[str] = mapped_column(String)
    decided_by: Mapped[str] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    actor_id: Mapped[str] = mapped_column(String)
    action: Mapped[str] = mapped_column(String)
    target_type: Mapped[str] = mapped_column(String)
    target_id: Mapped[str] = mapped_column(String)
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    sequence: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    previous_hash: Mapped[str] = mapped_column(String(64))
    event_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AuditChainHead(Base):
    __tablename__ = "audit_chain_heads"
    id: Mapped[str] = mapped_column(String, primary_key=True, default="global")
    sequence: Mapped[int] = mapped_column(Integer, default=0)
    event_hash: Mapped[str] = mapped_column(String(64), default="0" * 64)


class KillSwitch(Base):
    __tablename__ = "kill_switches"
    id: Mapped[str] = mapped_column(String, primary_key=True, default="global")
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    reason: Mapped[str] = mapped_column(String, default="")
    changed_by: Mapped[str] = mapped_column(String, default="system")
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./open_reception.sqlite3")
# psycopg3 호환: Railway PostgreSQL URL 변환
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
engine_args = (
    {"connect_args": {"check_same_thread": False, "timeout": 30}}
    if DATABASE_URL.startswith("sqlite")
    else {}
)
engine = create_engine(DATABASE_URL, **engine_args)
SessionLocal = sessionmaker(engine, expire_on_commit=False)

app = FastAPI(title="Luna Open Reception", version="0.4.0")

ADMIN_PERMISSIONS = {
    "security_admin": {"session:revoke", "account:disable", "passport:manage"},
    "steward_reviewer": {"steward:review", "matching:decide"},
    "safety_operator": {"kill_switch:change"},
    "admin": {"session:revoke", "account:disable", "passport:manage", "steward:review", "matching:decide", "kill_switch:change"},
}


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


# Run the same expensive password-verification path for unknown accounts to reduce
# account-enumeration signal from response timing.
DUMMY_PASSWORD_HASH = password_hash(secrets.token_urlsafe(32))


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def setting_int(name: str, default: int) -> int:
    try:
        return max(int(os.getenv(name, str(default))), 1)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc


def aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def locked_audit_head(db: Session) -> AuditChainHead | None:
    if db.bind.dialect.name == "sqlite":
        # SQLite ignores SELECT FOR UPDATE. This no-op write acquires the
        # database write lock before the caller reads and advances the head.
        db.execute(
            update(AuditChainHead)
            .where(AuditChainHead.id == "global")
            .values(sequence=AuditChainHead.sequence)
        )
        return db.get(AuditChainHead, "global")
    return db.get(AuditChainHead, "global", with_for_update=True)


def locked_human_passport(db: Session, passport_id: str) -> HumanPassport | None:
    if db.bind.dialect.name == "sqlite":
        # SQLite ignores SELECT FOR UPDATE. Acquire its database write lock
        # before reading so a waiter validates the latest committed status.
        db.execute(
            update(HumanPassport)
            .where(HumanPassport.id == passport_id)
            .values(status=HumanPassport.status)
        )
        return db.get(HumanPassport, passport_id)
    return db.scalar(
        select(HumanPassport)
        .where(HumanPassport.id == passport_id)
        .with_for_update()
    )


def locked_recommendation(db: Session, recommendation_id: str) -> MatchingRecommendation | None:
    if db.bind.dialect.name == "sqlite":
        db.execute(
            update(MatchingRecommendation)
            .where(MatchingRecommendation.id == recommendation_id)
            .values(status=MatchingRecommendation.status)
        )
        return db.get(MatchingRecommendation, recommendation_id)
    return db.scalar(
        select(MatchingRecommendation)
        .where(MatchingRecommendation.id == recommendation_id)
        .with_for_update()
    )


def audit(db: Session, actor: str, action: str, target_type: str, target_id: str, detail: dict | None = None):
    head = locked_audit_head(db)
    if head is None:
        head = AuditChainHead(id="global")
        db.add(head)
        db.flush()
    created_at = now()
    sequence = head.sequence + 1
    event_id = str(uuid4())
    normalized_detail = detail or {}
    canonical = json.dumps({
        "id": event_id,
        "sequence": sequence,
        "actor_id": actor,
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "detail": normalized_detail,
        "created_at": created_at.isoformat(),
        "previous_hash": head.event_hash,
    }, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    event_hash = hashlib.sha256(canonical.encode()).hexdigest()
    db.add(AuditEvent(
        id=event_id, actor_id=actor, action=action, target_type=target_type,
        target_id=target_id, detail=normalized_detail, sequence=sequence,
        previous_hash=head.event_hash, event_hash=event_hash, created_at=created_at,
    ))
    head.sequence = sequence
    head.event_hash = event_hash


def verify_audit_chain(db: Session) -> bool:
    # Audit writers serialize on this same row. Locking it before reading the
    # events prevents a concurrent append from advancing the head between the
    # event scan and the terminal head comparison.
    head = locked_audit_head(db)
    if head is None:
        return False
    previous_hash = "0" * 64
    expected_sequence = 1
    for event in db.scalars(select(AuditEvent).order_by(AuditEvent.sequence)).all():
        canonical = json.dumps({
            "id": event.id,
            "sequence": event.sequence,
            "actor_id": event.actor_id,
            "action": event.action,
            "target_type": event.target_type,
            "target_id": event.target_id,
            "detail": event.detail,
            "created_at": aware(event.created_at).isoformat(),
            "previous_hash": event.previous_hash,
        }, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        if (
            event.sequence != expected_sequence
            or event.previous_hash != previous_hash
            or not hmac.compare_digest(event.event_hash, hashlib.sha256(canonical.encode()).hexdigest())
        ):
            return False
        previous_hash = event.event_hash
        expected_sequence += 1
    return (
        head.sequence == expected_sequence - 1
        and hmac.compare_digest(head.event_hash, previous_hash)
    )


def current_session(
    authorization: Annotated[str | None, Header()] = None,
    db: Session = Depends(db_session),
) -> LoginSession:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Bearer token required")
    session = db.scalar(select(LoginSession).where(LoginSession.token_hash == token_hash(authorization[7:])))
    if not session or session.revoked or aware(session.expires_at) <= now():
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired session")
    return session


def current_user(session: LoginSession = Depends(current_session), db: Session = Depends(db_session)) -> User:
    user = db.get(User, session.user_id)
    if not user or user.disabled:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account disabled")
    return user


def require_permission(permission: str):
    def dependency(user: User = Depends(current_user), db: Session = Depends(db_session)) -> User:
        if permission not in ADMIN_PERMISSIONS.get(user.role, set()):
            audit(db, user.id, "authorization.denied", "permission", permission, {"role": user.role})
            db.commit()
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient Human administrator permission")
        return user
    return dependency


def revoke_sessions(db: Session, user_id: str, actor_id: str, reason: str) -> int:
    sessions = db.scalars(select(LoginSession).where(
        LoginSession.user_id == user_id, LoginSession.revoked.is_(False)
    )).all()
    for login_session in sessions:
        login_session.revoked = True
        login_session.revoked_at = now()
        login_session.revoked_by = actor_id
        login_session.revoke_reason = reason
    return len(sessions)


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
    request_type: str = "food_access_research"
    risk: Literal["low", "medium", "high"] = "low"
    required_permissions: list[str] = Field(default_factory=list)


class MatchingDecisionInput(BaseModel):
    action: Literal["approve", "reject", "reassign", "hold"]
    reason: str = Field(min_length=3, max_length=500)
    candidate_id: str | None = None


class KillInput(BaseModel):
    active: bool
    reason: str = Field(min_length=3, max_length=500)


class RevokeInput(BaseModel):
    reason: str = Field(min_length=3, max_length=500)
    disable_account: bool = False


class BootstrapInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=16, max_length=256)
    bootstrap_token: str = Field(min_length=32, max_length=512)


class PassportStatusInput(BaseModel):
    status: Literal["active", "suspended", "expired", "revoked"]
    reason: str = Field(min_length=3, max_length=500)


@app.on_event("startup")
def startup():
    with SessionLocal() as db:
        if not db.get(KillSwitch, "global"):
            db.add(KillSwitch())
        if not db.get(AiPassport, "luna"):
            db.add(AiPassport(
                id="luna", name="Luna", level="professional",
                domains=["reception", "food-desert", "research", "membership-guidance", "joint-purchase"],
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
    return {"status": "ok", "dry_run": True, "version": "0.4.0"}


@app.post("/auth/bootstrap", status_code=201)
def bootstrap_admin(payload: BootstrapInput, db: Session = Depends(db_session)):
    configured = os.getenv("ADMIN_BOOTSTRAP_TOKEN")
    if not configured or not hmac.compare_digest(payload.bootstrap_token, configured):
        audit(db, "anonymous", "bootstrap.denied", "user", payload.email.lower())
        db.commit()
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Bootstrap denied")
    if db.scalar(select(User).where(User.email == payload.email.lower())):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    user = User(email=payload.email.lower(), password_hash=password_hash(payload.password), role="admin")
    try:
        db.add(user)
        db.flush()
        # The fixed primary key is the durable, database-enforced one-time claim.
        # Concurrent transactions cannot both flush this row.
        db.add(BootstrapConsumption(id="admin", consumed_by=user.id))
        db.flush()
        audit(db, user.id, "bootstrap.admin_created", "user", user.id)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Bootstrap already consumed")
    return {"id": user.id, "role": user.role, "bootstrap_consumed": True}


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
    candidate_hash = user.password_hash if user else DUMMY_PASSWORD_HASH
    password_matches = password_valid(payload.password, candidate_hash)
    request_time = now()
    if user and user.locked_until and aware(user.locked_until) > request_time:
        audit(db, user.id, "login.blocked_locked", "user", user.id)
        db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    if not user or not password_matches:
        if user:
            threshold = setting_int("LOGIN_MAX_FAILURES", 5)
            lock_until = request_time + timedelta(minutes=setting_int("LOGIN_LOCKOUT_MINUTES", 15))
            incremented = db.execute(
                update(User)
                .where(
                    User.id == user.id,
                    (User.locked_until.is_(None)) | (User.locked_until <= request_time),
                )
                .values(
                    failed_login_count=User.failed_login_count + 1,
                    locked_until=case(
                        (User.failed_login_count + 1 >= threshold, lock_until),
                        else_=User.locked_until,
                    ),
                )
                .returning(User.failed_login_count, User.locked_until)
            ).one_or_none()
            if incremented is None:
                audit(db, user.id, "login.blocked_locked", "user", user.id)
            else:
                failure_count, updated_locked_until = incremented
                if updated_locked_until and aware(updated_locked_until) > request_time:
                    audit(db, user.id, "account.locked", "user", user.id)
                audit(db, user.id, "login.failed", "user", user.id, {"failure_count": failure_count})
        else:
            email_hash = hashlib.sha256(payload.email.lower().encode()).hexdigest()
            audit(db, "anonymous", "login.failed_unknown", "email_hash", email_hash)
        db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    if user.disabled:
        audit(db, user.id, "login.blocked_disabled", "user", user.id)
        db.commit()
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account disabled")
    reset = db.execute(
        update(User)
        .where(
            User.id == user.id,
            (User.locked_until.is_(None)) | (User.locked_until <= request_time),
        )
        .values(failed_login_count=0, locked_until=None)
        .returning(User.id)
    ).one_or_none()
    if reset is None:
        audit(db, user.id, "login.blocked_locked", "user", user.id)
        db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    token = secrets.token_urlsafe(32)
    ttl = setting_int("SESSION_TTL_MINUTES", 60)
    login_session = LoginSession(user_id=user.id, token_hash=token_hash(token), expires_at=now() + timedelta(minutes=ttl))
    db.add(login_session)
    db.flush()
    audit(db, user.id, "session.created", "session", login_session.id)
    db.commit()
    return {"access_token": token, "token_type": "bearer", "expires_in": ttl * 60}


@app.post("/auth/logout", status_code=204)
def logout(session: LoginSession = Depends(current_session), db: Session = Depends(db_session)):
    session.revoked, session.revoked_at = True, now()
    session.revoked_by, session.revoke_reason = session.user_id, "logout"
    audit(db, session.user_id, "session.revoked", "session", session.id, {"reason": "logout"})
    db.commit()


@app.post("/auth/logout-all")
def logout_all(user: User = Depends(current_user), db: Session = Depends(db_session)):
    count = revoke_sessions(db, user.id, user.id, "logout_all")
    audit(db, user.id, "sessions.revoked_all", "user", user.id, {"count": count})
    db.commit()
    return {"revoked_sessions": count}


@app.post("/admin/users/{user_id}/revoke")
def admin_revoke(
    user_id: str,
    payload: RevokeInput,
    admin: User = Depends(require_permission("session:revoke")),
    db: Session = Depends(db_session),
):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if payload.disable_account and "account:disable" not in ADMIN_PERMISSIONS.get(admin.role, set()):
        audit(db, admin.id, "authorization.denied", "permission", "account:disable", {"role": admin.role})
        db.commit()
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient Human administrator permission")
    count = revoke_sessions(db, target.id, admin.id, payload.reason)
    if payload.disable_account:
        target.disabled = True
    audit(db, admin.id, "admin.user_revoked", "user", target.id, {
        "sessions": count, "disabled": payload.disable_account, "reason": payload.reason,
    })
    db.commit()
    return {"user_id": target.id, "revoked_sessions": count, "disabled": target.disabled}


@app.put("/passport/human")
def upsert_passport(payload: PassportInput, user: User = Depends(current_user), db: Session = Depends(db_session)):
    passport = db.scalar(select(HumanPassport).where(HumanPassport.user_id == user.id))
    if passport:
        passport.display_name, passport.domains = payload.display_name, payload.domains
    else:
        passport = HumanPassport(user_id=user.id, display_name=payload.display_name, domains=payload.domains)
        db.add(passport)
    db.flush()
    if not db.scalar(select(HumanPassportStatusHistory).where(
        HumanPassportStatusHistory.passport_id == passport.id
    )):
        db.add(HumanPassportStatusHistory(
            passport_id=passport.id, from_status=None, to_status="active",
            reason="passport issued", changed_by=user.id,
        ))
    audit(db, user.id, "human_passport.upserted", "human_passport", passport.id)
    db.commit()
    return {"id": passport.id, "status": passport.status, "policy_version": passport.policy_version}


@app.post("/admin/passports/human/{passport_id}/status")
def change_human_passport_status(
    passport_id: str,
    payload: PassportStatusInput,
    admin: User = Depends(require_permission("passport:manage")),
    db: Session = Depends(db_session),
):
    passport = locked_human_passport(db, passport_id)
    if not passport:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Human Passport not found")
    allowed = {
        "active": {"suspended", "expired", "revoked"},
        "suspended": {"active", "expired", "revoked"},
        "expired": {"active", "revoked"},
        "revoked": set(),
    }
    if payload.status not in allowed.get(passport.status, set()):
        raise HTTPException(status.HTTP_409_CONFLICT, "Invalid Human Passport status transition")
    previous = passport.status
    passport.status = payload.status
    passport.status_reason = payload.reason
    passport.status_changed_at = now()
    db.add(HumanPassportStatusHistory(
        passport_id=passport.id, from_status=previous, to_status=payload.status,
        reason=payload.reason, changed_by=admin.id,
    ))
    audit(db, admin.id, "human_passport.status_changed", "human_passport", passport.id, {
        "from": previous, "to": payload.status, "reason": payload.reason,
    })
    db.commit()
    return {"id": passport.id, "status": passport.status}


@app.get("/admin/audit/verify")
def audit_verify(
    admin: User = Depends(require_permission("passport:manage")),
    db: Session = Depends(db_session),
):
    return {"valid": verify_audit_chain(db)}


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
def review_steward(application_id: str, payload: ReviewInput, admin: User = Depends(require_permission("steward:review")), db: Session = Depends(db_session)):
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
    try:
        domain_pack = get_domain_pack(payload.domain)
        policy = domain_pack.policy_for(payload.request_type)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    request = MatchRequest(
        requester_id=user.id, domain=payload.domain, risk=payload.risk,
        required_permissions=payload.required_permissions,
    )
    db.add(request)
    db.flush()
    recommendation = MatchingRecommendation(
        request_id=request.id,
        domain_pack_version=DOMAIN_PACK_VERSION,
        policy_version=MATCHING_POLICY_VERSION,
        rationale={"request_type": payload.request_type, "supervision": policy.supervision_level},
    )
    db.add(recommendation)
    db.flush()
    evaluated = []
    agents = db.scalars(select(AiPassport).order_by(AiPassport.id)).all()
    active_ids = {agent.id for agent in agents if agent.status == "active"}
    for agent in agents:
        evaluation = evaluate_candidate(
            policy=policy,
            request_risk=payload.risk,
            mandate_permissions=payload.required_permissions,
            agent_id=agent.id,
            agent_level=agent.level,
            agent_domains=agent.domains,
            passport_permissions=agent.permissions,
            spirit_score=agent.spirit_score,
            agent_status=agent.status,
            supervisor_active=bool(agent.mentor_agent and agent.mentor_agent in active_ids),
        )
        evaluated.append((agent, evaluation))
    eligible = sorted(
        ((agent, result) for agent, result in evaluated if result.eligible),
        key=lambda pair: (-pair[1].score, pair[0].id),
    )
    ranks = {agent.id: rank for rank, (agent, _) in enumerate(eligible, 1)}
    for agent, result in evaluated:
        db.add(MatchingCandidate(
            recommendation_id=recommendation.id,
            agent_passport_id=agent.id,
            agent_kind="jr_agent" if agent.level == "junior" else "steward_ai",
            rank=ranks.get(agent.id),
            score=result.score,
            eligible=result.eligible,
            evidence=dict(result.evidence),
            exclusion_reasons=list(result.exclusion_reasons),
            supervisor_agent_id=agent.mentor_agent if agent.level == "junior" else None,
        ))
    candidates = [{
        "candidate_id": next_candidate.id,
        "agent_id": agent.id,
        "name": agent.name,
        "level": agent.level,
        "rank": ranks[agent.id],
        "score": result.score,
        "requires_supervision": agent.level == "junior",
        "supervisor_agent_id": agent.mentor_agent if agent.level == "junior" else None,
        "allowed_actions": agent.permissions,
        "evidence": dict(result.evidence),
    } for agent, result in eligible for next_candidate in [
        db.scalar(select(MatchingCandidate).where(
            MatchingCandidate.recommendation_id == recommendation.id,
            MatchingCandidate.agent_passport_id == agent.id,
        ))
    ]]
    audit(db, user.id, "matching.recommended", "matching_recommendation", recommendation.id, {
        "request_id": request.id,
        "policy_version": MATCHING_POLICY_VERSION,
        "candidate_ids": [c["agent_id"] for c in candidates[:3]],
    })
    db.commit()
    return {
        "request_id": request.id,
        "recommendation_id": recommendation.id,
        "status": "recommendation_only",
        "policy_version": MATCHING_POLICY_VERSION,
        "human_approval_required": True,
        "candidates": candidates[:3],
    }


@app.post("/admin/matching/recommendations/{recommendation_id}/decision")
def decide_matching(
    recommendation_id: str,
    payload: MatchingDecisionInput,
    admin: User = Depends(require_permission("matching:decide")),
    db: Session = Depends(db_session),
):
    enforce_kill_switch(db)
    recommendation = locked_recommendation(db, recommendation_id)
    if not recommendation:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recommendation not found")
    if recommendation.status != "recommended":
        raise HTTPException(status.HTTP_409_CONFLICT, "Recommendation already decided")
    target_status = {
        "approve": "approved",
        "reject": "rejected",
        "reassign": "reassignment_requested",
        "hold": "needs_evidence",
    }[payload.action]
    if payload.action == "approve":
        if not payload.candidate_id:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "candidate_id required")
        candidate = db.get(MatchingCandidate, payload.candidate_id)
        if not candidate or candidate.recommendation_id != recommendation.id or not candidate.eligible:
            raise HTTPException(status.HTTP_409_CONFLICT, "Eligible candidate required")
        agent = db.get(AiPassport, candidate.agent_passport_id)
        if not agent or agent.status != "active" or agent.spirit_score < 0.4:
            raise HTTPException(status.HTTP_409_CONFLICT, "Candidate is no longer eligible")
        if agent.level == "junior":
            supervisor = db.get(AiPassport, candidate.supervisor_agent_id)
            if not supervisor or supervisor.status != "active":
                raise HTTPException(status.HTTP_409_CONFLICT, "Active supervisor required")
    previous = recommendation.status
    recommendation.status = target_status
    db.add(MatchingDecision(
        recommendation_id=recommendation.id,
        action=payload.action,
        from_status=previous,
        to_status=target_status,
        decided_by=admin.id,
        reason=payload.reason,
    ))
    audit(db, admin.id, f"matching.{payload.action}", "matching_recommendation", recommendation.id, {
        "from": previous, "to": target_status, "candidate_id": payload.candidate_id,
    })
    db.commit()
    return {"recommendation_id": recommendation.id, "status": target_status}


@app.post("/admin/kill-switch")
def set_kill_switch(payload: KillInput, admin: User = Depends(require_permission("kill_switch:change")), db: Session = Depends(db_session)):
    switch = db.get(KillSwitch, "global")
    switch.active, switch.reason, switch.changed_by, switch.changed_at = payload.active, payload.reason, admin.id, now()
    audit(db, admin.id, "kill_switch.changed", "kill_switch", "global", {"active": payload.active, "reason": payload.reason})
    db.commit()
    return {"active": switch.active, "reason": switch.reason}
