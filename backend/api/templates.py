import re
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models import EmailTemplate, User, Contact
from backend.schemas import (
    EmailTemplateOut, EmailTemplateCreate, EmailTemplateUpdate,
    TemplatePreviewRequest, TemplatePreviewOut
)
from backend.campaigns.renderer import TemplateRenderer
from backend.api.deps import get_current_user, log_audit

router = APIRouter(prefix="/templates", tags=["Templates"])


def extract_variables(text: str) -> List[str]:
    found = re.findall(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}", text)
    return sorted(list(set(found)))


@router.get("", response_model=List[EmailTemplateOut])
def list_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    templates = db.query(EmailTemplate).filter(
        EmailTemplate.organization_id == current_user.organization_id
    ).order_by(EmailTemplate.created_at.desc()).all()
    return templates


@router.post("", response_model=EmailTemplateOut)
def create_template(
    req: EmailTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    vars_found = extract_variables(req.subject + " " + req.body_markdown)
    html_rendered = TemplateRenderer.markdown_to_html(req.body_markdown)

    tmpl = EmailTemplate(
        id=uuid.uuid4(),
        organization_id=current_user.organization_id,
        name=req.name,
        subject=req.subject,
        body_markdown=req.body_markdown,
        body_html=html_rendered,
        variables=vars_found
    )
    db.add(tmpl)
    db.commit()
    db.refresh(tmpl)

    log_audit(
        db,
        action="TEMPLATE_CREATED",
        target_type="TEMPLATE",
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        target_id=str(tmpl.id)
    )
    return tmpl


@router.get("/{template_id}", response_model=EmailTemplateOut)
def get_template(
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tmpl = db.query(EmailTemplate).filter(
        EmailTemplate.id == template_id,
        EmailTemplate.organization_id == current_user.organization_id
    ).first()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")
    return tmpl


@router.patch("/{template_id}", response_model=EmailTemplateOut)
def update_template(
    template_id: uuid.UUID,
    req: EmailTemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tmpl = db.query(EmailTemplate).filter(
        EmailTemplate.id == template_id,
        EmailTemplate.organization_id == current_user.organization_id
    ).first()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")

    if req.name is not None:
        tmpl.name = req.name
    if req.subject is not None:
        tmpl.subject = req.subject
    if req.body_markdown is not None:
        tmpl.body_markdown = req.body_markdown
        tmpl.body_html = TemplateRenderer.markdown_to_html(req.body_markdown)

    tmpl.variables = extract_variables(tmpl.subject + " " + tmpl.body_markdown)

    db.commit()
    db.refresh(tmpl)

    log_audit(
        db,
        action="TEMPLATE_UPDATED",
        target_type="TEMPLATE",
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        target_id=str(tmpl.id)
    )
    return tmpl


@router.delete("/{template_id}")
def delete_template(
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tmpl = db.query(EmailTemplate).filter(
        EmailTemplate.id == template_id,
        EmailTemplate.organization_id == current_user.organization_id
    ).first()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")

    db.delete(tmpl)
    db.commit()

    log_audit(
        db,
        action="TEMPLATE_DELETED",
        target_type="TEMPLATE",
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        target_id=str(template_id)
    )
    return {"status": "success", "message": f"Template {template_id} deleted."}


@router.post("/preview", response_model=TemplatePreviewOut)
def preview_template(
    req: TemplatePreviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tmpl = db.query(EmailTemplate).filter(
        EmailTemplate.id == req.template_id,
        EmailTemplate.organization_id == current_user.organization_id
    ).first()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")

    context = {
        "first_name": "Jordan",
        "full_name": "Jordan Lee",
        "project_name": "DistributedMesh",
        "organization_name": current_user.organization.name if current_user.organization else "OpenDev",
        "unsubscribe_url": "http://localhost:8000/api/v1/suppression/unsubscribe?token=sample"
    }

    if req.contact_id:
        contact = db.query(Contact).filter(
            Contact.id == req.contact_id,
            Contact.organization_id == current_user.organization_id
        ).first()
        if contact:
            first_name = (contact.full_name or "").split()[0] if contact.full_name else "there"
            context["first_name"] = first_name
            context["full_name"] = contact.full_name or "Maintainer"
            if contact.project:
                context["project_name"] = contact.project.name

    if req.sample_context:
        context.update(req.sample_context)

    rendered_subj = TemplateRenderer.render(tmpl.subject, context)
    rendered_body = TemplateRenderer.render(tmpl.body_markdown, context)
    rendered_html = TemplateRenderer.markdown_to_html(rendered_body)

    return TemplatePreviewOut(
        subject=rendered_subj,
        body_markdown=rendered_body,
        body_html=rendered_html,
        resolved_variables=context
    )
