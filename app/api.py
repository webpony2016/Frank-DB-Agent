from fastapi import APIRouter, Depends
from .workspaces import context, Scope
from .serializers import bootstrap

router = APIRouter(prefix="/api")


@router.get("/bootstrap")
def get_bootstrap(scope: Scope = Depends(context)):
    return bootstrap(scope.session, scope.workspace_id)


from fastapi import Response
from .schemas import JobBriefInput
from .assistant import prepare_brief
from .jobs import convert_inquiry
from .serializers import get_job_detail


@router.post("/inquiries/{inquiry_id}/brief")
def brief(inquiry_id: str, scope: Scope = Depends(context)):
    return prepare_brief(scope.session, scope.workspace_id, inquiry_id)


@router.post("/inquiries/{inquiry_id}/job")
def convert(inquiry_id: str, data: JobBriefInput, response: Response, scope: Scope = Depends(context)):
    job, created = convert_inquiry(scope.session, scope.workspace_id, inquiry_id, data)
    response.status_code = 201 if created else 200
    return get_job_detail(scope.session, scope.workspace_id, job.id)


@router.get("/jobs/{job_id}")
def detail(job_id: str, scope: Scope = Depends(context)):
    return get_job_detail(scope.session, scope.workspace_id, job_id)


from .schemas import QuoteInput, VersionInput
from .quotes import save_quote, approve_quote


@router.post("/jobs/{job_id}/quotes")
def quote_save(job_id: str, data: QuoteInput, scope: Scope = Depends(context)):
    save_quote(scope.session, scope.workspace_id, job_id, data.expected_version, data.lines)
    return get_job_detail(scope.session, scope.workspace_id, job_id)


@router.post("/jobs/{job_id}/quotes/{quote_id}/approve")
def quote_approve(job_id: str, quote_id: str, data: VersionInput, scope: Scope = Depends(context)):
    approve_quote(scope.session, scope.workspace_id, job_id, quote_id, data.expected_version)
    return get_job_detail(scope.session, scope.workspace_id, job_id)


from .schemas import AssignmentInput, StatusInput
from .scheduling import assign_job
from .jobs import transition_job


@router.put("/jobs/{job_id}/assignment")
def assignment_save(job_id: str, data: AssignmentInput, scope: Scope = Depends(context)):
    assign_job(scope.session, scope.workspace_id, job_id, data)
    return get_job_detail(scope.session, scope.workspace_id, job_id)


@router.post("/jobs/{job_id}/status")
def status_save(job_id: str, data: StatusInput, scope: Scope = Depends(context)):
    transition_job(scope.session, scope.workspace_id, job_id, data.expected_version, data.status)
    return get_job_detail(scope.session, scope.workspace_id, job_id)


from .schemas import NoteInput, DraftInput, PreviewInput
from .communications import add_note, create_draft, update_draft
from .integrations import integration_list, preview_integration


@router.post("/jobs/{job_id}/notes")
def note_save(job_id: str, data: NoteInput, scope: Scope = Depends(context)):
    add_note(scope.session, scope.workspace_id, job_id, data.expected_version, data.text)
    return get_job_detail(scope.session, scope.workspace_id, job_id)


@router.post("/jobs/{job_id}/drafts")
def draft_create(job_id: str, data: VersionInput, scope: Scope = Depends(context)):
    create_draft(scope.session, scope.workspace_id, job_id, data.expected_version)
    return get_job_detail(scope.session, scope.workspace_id, job_id)


@router.put("/jobs/{job_id}/drafts/{draft_id}")
def draft_save(job_id: str, draft_id: str, data: DraftInput, scope: Scope = Depends(context)):
    update_draft(scope.session, scope.workspace_id, job_id, draft_id, data)
    return get_job_detail(scope.session, scope.workspace_id, job_id)


@router.get("/integrations")
def integrations(scope: Scope = Depends(context)):
    return integration_list(scope.session, scope.workspace_id)


@router.post("/jobs/{job_id}/integration-previews")
def integration_preview(job_id: str, data: PreviewInput, scope: Scope = Depends(context)):
    preview = preview_integration(scope.session, scope.workspace_id, job_id, data.expected_version, data.connector)
    return dict(get_job_detail(scope.session, scope.workspace_id, job_id), preview=preview)

