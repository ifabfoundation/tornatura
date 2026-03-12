from fastapi import APIRouter
from fastapi.responses import Response

from core.serializers import FormTemplateRenderPayload
from core.services.forms_services import FormsServices


router = APIRouter()


@router.post(
    "/forms/form-01/informativa-pmi/pdf",
    operation_id="render_form_01_informativa_pmi_pdf",
    summary="Render FORM_01 Informativa PMI as PDF",
    response_description="Generated PDF document",
)
async def render_form_01_informativa_pmi_pdf(payload: FormTemplateRenderPayload) -> Response:
    forms_services = FormsServices()
    pdf_content = forms_services.render_form_01_pdf(payload.data)

    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=FORM_01_Informativa_PMI_partecipanti.pdf"
        },
    )
