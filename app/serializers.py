from sqlalchemy import select
from .models import Customer, Inquiry, Job, Crew, Equipment, Quote, QuoteLine, Assignment, ActivityEvent, CommunicationDraft
from .seed import business_date


def rows(session, model, workspace_id):
    return session.scalars(select(model).where(model.workspace_id == workspace_id)).all()


def record(row):
    return {c.name: (getattr(row, c.name).isoformat() if hasattr(getattr(row, c.name), "isoformat") else getattr(row, c.name))
            for c in row.__table__.columns if c.name not in {"workspace_id", "token_hash"}}


def money(cents):
    return f"{cents // 100}.{cents % 100:02d}"


def job_summary(session, job):
    result = record(job)
    customer = session.scalar(select(Customer).where(Customer.id == job.customer_id, Customer.workspace_id == job.workspace_id))
    result["customer_name"] = customer.name
    quotes = session.scalars(select(Quote).where(Quote.job_id == job.id, Quote.workspace_id == job.workspace_id).order_by(Quote.revision)).all()
    result["quote_total"] = money(quotes[-1].total_cents) if quotes else None
    result["current_quote_id"] = quotes[-1].id if quotes else None
    return result


def bootstrap(session, workspace_id):
    jobs = rows(session, Job, workspace_id)
    linked = {j.source_inquiry_id: j.id for j in jobs if j.source_inquiry_id}
    inquiries = [dict(record(i), job_id=linked.get(i.id)) for i in rows(session, Inquiry, workspace_id)]
    draft_cents = 0
    for job in jobs:
        if job.status == "draft":
            current = session.scalar(select(Quote).where(Quote.job_id == job.id, Quote.workspace_id == workspace_id).order_by(Quote.revision.desc()))
            draft_cents += current.total_cents if current else 0
    assignments = rows(session, Assignment, workspace_id)
    active_ids = {j.id for j in jobs if j.status != "completed"}
    return dict(mode="sample", business_date=business_date().isoformat(),
                customers=[record(c) for c in rows(session, Customer, workspace_id)], inquiries=inquiries,
                jobs=[job_summary(session, j) for j in jobs],
                crews=[record(c) for c in rows(session, Crew, workspace_id)],
                equipment=[record(e) for e in rows(session, Equipment, workspace_id)],
                assignments=[record(a) for a in assignments],
                metrics=dict(active_jobs=sum(j.status != "completed" for j in jobs), inquiries=sum(not i["job_id"] for i in inquiries),
                             draft_quote_value=money(draft_cents), upcoming=sum(a.end_date >= business_date() and a.job_id in active_ids for a in assignments)),
                activity=[record(e) for e in sorted(rows(session, ActivityEvent, workspace_id), key=lambda e: (e.created_at, e.id))][-20:])


def get_job_detail(session, workspace_id, job_id):
    from .jobs import require_job
    job = require_job(session, workspace_id, job_id)
    result = job_summary(session, job)
    quotes = session.scalars(select(Quote).where(Quote.workspace_id == workspace_id, Quote.job_id == job_id).order_by(Quote.revision)).all()
    result["quotes"] = []
    for quote in quotes:
        lines = session.scalars(select(QuoteLine).where(QuoteLine.workspace_id == workspace_id, QuoteLine.quote_id == quote.id).order_by(QuoteLine.position)).all()
        result["quotes"].append(dict(record(quote), total=money(quote.total_cents),
                                     lines=[dict(record(line), total=money(line.total_cents)) for line in lines]))
    assignment = session.scalar(select(Assignment).where(Assignment.workspace_id == workspace_id, Assignment.job_id == job_id))
    result["assignment"] = record(assignment) if assignment else None
    result["drafts"] = [dict(record(d), mode="sample", state="draft") for d in session.scalars(select(CommunicationDraft).where(
        CommunicationDraft.workspace_id == workspace_id, CommunicationDraft.job_id == job_id).order_by(CommunicationDraft.created_at, CommunicationDraft.id))]
    result["activity"] = [record(e) for e in session.scalars(select(ActivityEvent).where(
        ActivityEvent.workspace_id == workspace_id, ActivityEvent.job_id == job_id).order_by(ActivityEvent.created_at, ActivityEvent.id))]
    return result
