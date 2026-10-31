from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models import Project, User
from backend.schemas import ProjectOut, ProjectCreate
from backend.api.deps import get_current_user, log_audit

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=List[ProjectOut])
def list_projects(
    query: Optional[str] = None,
    language: Optional[str] = None,
    min_stars: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(Project).filter(Project.organization_id == current_user.organization_id)
    if query:
        q = q.filter(
            (Project.name.ilike(f"%{query}%")) |
            (Project.full_name.ilike(f"%{query}%")) |
            (Project.description.ilike(f"%{query}%"))
        )
    if language:
        q = q.filter(Project.language.ilike(f"%{language}%"))
    if min_stars is not None:
        q = q.filter(Project.stars_count >= min_stars)

    projects = q.order_by(Project.stars_count.desc()).offset(skip).limit(limit).all()
    return projects


@router.post("", response_model=ProjectOut)
def create_project(
    req: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(Project).filter(
        Project.organization_id == current_user.organization_id,
        Project.full_name == req.full_name
    ).first()
    if existing:
        return existing

    proj = Project(
        id=uuid.uuid4(),
        organization_id=current_user.organization_id,
        name=req.name,
        full_name=req.full_name,
        description=req.description,
        owner=req.owner,
        stars_count=req.stars_count,
        forks_count=req.forks_count,
        language=req.language,
        topics=req.topics,
        repository_url=req.repository_url,
        homepage_url=req.homepage_url,
        contributing_url=req.contributing_url
    )
    db.add(proj)
    db.commit()
    db.refresh(proj)

    log_audit(
        db,
        action="PROJECT_CREATED",
        target_type="PROJECT",
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        target_id=str(proj.id)
    )
    return proj


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    proj = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == current_user.organization_id
    ).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return proj


@router.delete("/{project_id}")
def delete_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    proj = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == current_user.organization_id
    ).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(proj)
    db.commit()

    log_audit(
        db,
        action="PROJECT_DELETED",
        target_type="PROJECT",
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        target_id=str(project_id)
    )
    return {"status": "success", "message": f"Project {project_id} deleted."}
