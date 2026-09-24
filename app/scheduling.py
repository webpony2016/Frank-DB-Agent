from sqlalchemy import select, or_
from .models import Assignment, Crew, Equipment
from .jobs import require_job, require_record, check_version, event
from .quotes import current_quote
from .errors import DomainError


def assign_job(session, workspace_id, job_id, assignment):
    job = require_job(session, workspace_id, job_id)
    check_version(job, assignment.expected_version)
    quote = current_quote(session, workspace_id, job_id)
    if job.status not in {"quoted", "scheduled"} or not quote or quote.state != "approved":
        raise DomainError(409, "Approve the current quote before scheduling. Only scheduled jobs can be rescheduled.")
    crew = require_record(session, Crew, workspace_id, assignment.crew_id)
    equipment = require_record(session, Equipment, workspace_id, assignment.equipment_id)
    conflict = session.scalar(select(Assignment).where(
        Assignment.workspace_id == workspace_id, Assignment.job_id != job_id,
        Assignment.start_date <= assignment.end_date, Assignment.end_date >= assignment.start_date,
        or_(Assignment.crew_id == crew.id, Assignment.equipment_id == equipment.id)))
    if conflict:
        resource = crew.name if conflict.crew_id == crew.id else equipment.name
        raise DomainError(409, f"Scheduling conflict: {resource} is reserved from {conflict.start_date} through {conflict.end_date}. Choose another resource or date.")
    existing = session.scalar(select(Assignment).where(Assignment.workspace_id == workspace_id, Assignment.job_id == job_id))
    if existing is None:
        existing = Assignment(workspace_id=workspace_id, job_id=job_id)
        session.add(existing)
    for key, value in assignment.model_dump(exclude={"expected_version"}).items():
        setattr(existing, key, value)
    job.status = "scheduled"
    event(session, job, "schedule", f"{crew.name} and {equipment.name} assigned: {assignment.start_date} through {assignment.end_date}.")
    return job
