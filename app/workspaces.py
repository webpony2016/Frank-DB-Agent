import hashlib
import secrets
from dataclasses import dataclass
from fastapi import Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from .db import transaction
from .models import Workspace
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
    with transaction(request.app.state.engine, write=create or request.method != "GET") as session:
        workspace = session.scalar(select(Workspace).where(Workspace.token_hash == digest)) if token else None
        if workspace is None:
            if not create:
                raise DomainError(401, "Your demo workspace is not available. Reload the page to start again.")
            token = secrets.token_urlsafe(32)
            workspace = Workspace(token_hash=hashlib.sha256(token.encode()).hexdigest())
            session.add(workspace)
            session.flush()
            seed_workspace(session, workspace.id, business_date())
            response.set_cookie("frank_workspace", token, httponly=True, samesite="lax", secure=request.app.state.settings.cookie_secure,
                                max_age=60 * 60 * 24 * 7)
        yield Scope(session, workspace.id)


def reset_workspace(session, workspace_id):
    from sqlalchemy import delete
    from .models import (QuoteLine, Quote, Assignment, CommunicationDraft, ActivityEvent,
                         IntegrationPreview, Job, Inquiry, Customer, Crew, Equipment)
    for model in (QuoteLine, Quote, Assignment, CommunicationDraft, ActivityEvent,
                  IntegrationPreview, Job, Inquiry, Customer, Crew, Equipment):
        session.execute(delete(model).where(model.workspace_id == workspace_id))
    session.flush()
    seed_workspace(session, workspace_id, business_date())
