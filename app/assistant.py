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
