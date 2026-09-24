from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import select
from .models import Quote, QuoteLine
from .jobs import require_job, require_record, check_version, event
from .errors import DomainError


def line_cents(quantity, unit_price):
    return int((quantity * unit_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) * 100)


def quote_total_cents(lines):
    total = sum(line_cents(line.quantity, line.unit_price) for line in lines)
    if total > 10_000_000_000:
        raise DomainError(422, "The illustrative quote total exceeds CAD 100,000,000.00.")
    return total


def current_quote(session, workspace_id, job_id):
    return session.scalar(select(Quote).where(Quote.workspace_id == workspace_id, Quote.job_id == job_id).order_by(Quote.revision.desc()))


def save_quote(session, workspace_id, job_id, expected_version, lines):
    job = require_job(session, workspace_id, job_id)
    check_version(job, expected_version)
    if job.status not in {"draft", "quoted"}:
        raise DomainError(409, "Quotes cannot be changed after a job has been scheduled.")
    total = quote_total_cents(lines)
    previous = current_quote(session, workspace_id, job_id)
    quote = Quote(workspace_id=workspace_id, job_id=job_id, revision=previous.revision + 1 if previous else 1,
                  state="draft", total_cents=total)
    session.add(quote)
    session.flush()
    for index, line in enumerate(lines):
        session.add(QuoteLine(workspace_id=workspace_id, quote_id=quote.id, position=index, description=line.description,
                              quantity=str(line.quantity), unit_price=f"{line.unit_price:.2f}", total_cents=line_cents(line.quantity, line.unit_price)))
    job.status = "draft"
    event(session, job, "quote", f"Quote revision {quote.revision} saved for internal review.")
    return job


def approve_quote(session, workspace_id, job_id, quote_id, expected_version):
    job = require_job(session, workspace_id, job_id)
    quote = require_record(session, Quote, workspace_id, quote_id)
    if quote.job_id != job_id:
        raise DomainError(404, "Quote not found for this job.")
    check_version(job, expected_version)
    latest = current_quote(session, workspace_id, job_id)
    if not latest or latest.id != quote_id or quote.state != "draft" or job.status != "draft":
        raise DomainError(409, "Only the current draft quote can be approved.")
    quote.state = "approved"
    job.status = "quoted"
    event(session, job, "approval", f"Quote revision {quote.revision} approved internally. Customer acceptance is not recorded.")
    return job
