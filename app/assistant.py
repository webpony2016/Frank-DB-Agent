from copy import deepcopy
from .jobs import require_record
from .models import Inquiry


def prepare_brief(session, workspace_id, inquiry_id):
    inquiry = require_record(session, Inquiry, workspace_id, inquiry_id)
    if inquiry.sample_key in {"example-1", "example-2", "example-3"}:
        return dict(mode="sample", provenance="prepared-example", brief=deepcopy(inquiry.brief))
    return dict(mode="sample", provenance="manual-entry-required",
                brief=dict(customer_id=inquiry.customer_id, title=inquiry.subject, site="", service="",
                           requested_start=None, requested_end=None,
                           missing_information=["No prepared example is available. Enter and review the job details manually."]))


def customer_update(session, workspace_id, job):
    from sqlalchemy import select
    from .models import Customer, Assignment
    customer = require_record(session, Customer, workspace_id, job.customer_id)
    assignment = session.scalar(select(Assignment).where(Assignment.workspace_id == workspace_id, Assignment.job_id == job.id))
    if assignment:
        schedule = f"Work dates on record: {assignment.start_date} through {assignment.end_date} (inclusive)."
    else:
        schedule = "Scheduling is pending. We will confirm dates after internal quote review and resource planning."
    body = (f"Hi {customer.contact},\n\nHere is an update on {job.title} at {job.site}.\n\n"
            f"Current project status: {job.status.replace('_', ' ')}.\n{schedule}\n\n"
            "Please let us know if your site access or project requirements have changed.\n\nThank you,\nOperations team")
    return f"Project update — {job.title}"[:200], body
