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

