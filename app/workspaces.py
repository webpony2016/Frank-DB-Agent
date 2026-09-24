import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from fastapi import Request, Response
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from .db import transaction
from .models import Workspace, ActivityEvent
from .seed import seed_workspace, business_date
from .errors import DomainError


@dataclass
class Scope:
    session: Session
    workspace_id: str


def context(request: Request, response: Response):
    token = request.cookies.get("frank_workspace", "")
    digest = hashlib.sha256(token.encode()).hexdigest()
    create = request.url.path == "/api/bootstrap"
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    settings = request.app.state.settings
    with transaction(request.app.state.engine, write=create or request.method != "GET") as session:
        workspace = session.scalar(select(Workspace).where(Workspace.token_hash == digest)) if token else None
        if workspace is not None and workspace.created_at <= cutoff:
            workspace = None
        if workspace is None:
            if not create:
                raise DomainError(401, "Your demo workspace is not available. Reload the page to start again.")
            for expired in session.scalars(select(Workspace).where(Workspace.created_at <= cutoff)).all():
                reset_workspace(session, expired.id, reseed=False)
                session.delete(expired)
            session.flush()
            if session.scalar(select(func.count()).select_from(Workspace)) >= settings.max_workspaces:
                raise DomainError(429, "The sample demo has reached its visitor capacity. Please try again later.")
            token = secrets.token_urlsafe(32)
            workspace = Workspace(token_hash=hashlib.sha256(token.encode()).hexdigest())
            session.add(workspace)
            session.flush()
            seed_workspace(session, workspace.id, business_date())
            response.set_cookie("frank_workspace", token, httponly=True, samesite="lax", secure=settings.cookie_secure,
                                max_age=60 * 60 * 24 * 7)
        if request.method != "GET" and request.url.path != "/api/reset":
            count = session.scalar(select(func.count()).select_from(ActivityEvent).where(ActivityEvent.workspace_id == workspace.id))
            if count >= settings.max_events:
                raise DomainError(429, "Your sample workspace is full. Reset sample data to start a fresh demonstration.")
        yield Scope(session, workspace.id)


def reset_workspace(session, workspace_id, reseed=True):
    from sqlalchemy import delete
    from .models import (QuoteLine, Quote, Assignment, CommunicationDraft, ActivityEvent,
                         IntegrationPreview, Job, Inquiry, Customer, Crew, Equipment)
    for model in (QuoteLine, Quote, Assignment, CommunicationDraft, ActivityEvent,
                  IntegrationPreview, Job, Inquiry, Customer, Crew, Equipment):
        session.execute(delete(model).where(model.workspace_id == workspace_id))
    session.flush()
    if reseed:
        seed_workspace(session, workspace_id, business_date())
