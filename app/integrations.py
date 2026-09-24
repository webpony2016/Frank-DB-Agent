from sqlalchemy import select
from .models import IntegrationPreview, Customer
from .jobs import require_job, check_version, event, require_record
from .serializers import get_job_detail, record
from .errors import DomainError

CONNECTORS = [
    dict(id="quickbooks", name="QuickBooks", category="Accounting", description="Review estimate line items before a future accounting sync.",
         mapping={"customer_name":"Customer display name", "lines":"Estimate line items", "amount_cad":"Estimate subtotal (CAD, before tax)"}),
    dict(id="email_calendar", name="Email & Calendar", category="Communications", description="Preview a calendar event from the saved job assignment.",
         mapping={"title":"Event title", "start_date":"First work day", "end_date":"Last work day (inclusive)", "site":"Location"}),
    dict(id="crm", name="CRM", category="Customer relationships", description="Preview customer and project details for a future CRM sync.",
         mapping={"customer_name":"Account name", "title":"Opportunity name", "status":"Internal project status"}),
]


def preview_record(row):
    connector = next(c for c in CONNECTORS if c["id"] == row.connector)
    return dict(record(row), mode="sample", connected=False, sent=False, mapping=connector["mapping"])


def integration_list(session, workspace_id):
    history = session.scalars(select(IntegrationPreview).where(IntegrationPreview.workspace_id == workspace_id)
                              .order_by(IntegrationPreview.created_at, IntegrationPreview.id)).all()
    return dict(connectors=[dict(c, connected=False, mode="sample") for c in CONNECTORS],
                history=[preview_record(p) for p in history][-30:])


def preview_integration(session, workspace_id, job_id, expected_version, connector):
    job = require_job(session, workspace_id, job_id)
    check_version(job, expected_version)
    detail = get_job_detail(session, workspace_id, job_id)
    customer = require_record(session, Customer, workspace_id, job.customer_id)
    payload = dict(job_id=job.id, title=job.title, customer_name=customer.name, status=job.status)
    if connector == "quickbooks":
        if not detail["quotes"]:
            raise DomainError(409, "Save a quote before previewing an accounting estimate.")
        quote = detail["quotes"][-1]
        payload.update(currency="CAD", amount_cad=quote["total"], tax_included=False, revision=quote["revision"],
                       lines=[{key: line[key] for key in ("description", "quantity", "unit_price", "total")} for line in quote["lines"]])
    elif connector == "email_calendar":
        if not detail["assignment"]:
            raise DomainError(409, "Schedule the job before previewing a calendar event.")
        payload.update({key: detail["assignment"][key] for key in ("start_date", "end_date", "crew_id", "equipment_id")})
        payload.update(site=job.site, date_semantics="Inclusive all-day Toronto business dates")
    elif connector != "crm":
        raise DomainError(422, "Unknown preview connector.")
    preview = IntegrationPreview(workspace_id=workspace_id, job_id=job_id, connector=connector, payload=payload)
    session.add(preview)
    event(session, job, "preview", f"Local {connector.replace('_', ' ')} preview created. No external connection or transmission.")
    return preview_record(preview)
