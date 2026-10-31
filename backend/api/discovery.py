import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from backend.database.session import get_db, SessionLocal
from backend.models import (
    User, Project, Contact, ContactSource, DiscoveryJob, JobStatus,
    SourceCategory, VerificationRecord
)
from backend.schemas import (
    DiscoveryQuery, DiscoveryJobOut, ProjectOut
)
from backend.discovery.github_adapter import GitHubAdapter
from backend.discovery.website_adapter import WebsiteAdapter
from backend.extraction.extractor import ContactExtractor
from backend.verification.dns_verifier import DNSVerifier
from backend.api.deps import get_current_user, log_audit

router = APIRouter(prefix="/discovery", tags=["Discovery"])


async def run_discovery_pipeline(
    job_id: uuid.UUID,
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    query: str,
    language: Optional[str],
    min_stars: int,
    max_results: int,
    scan_sources: bool
):
    db: Session = SessionLocal()
    try:
        job = db.query(DiscoveryJob).filter(DiscoveryJob.id == job_id).first()
        if not job:
            return

        job.status = JobStatus.RUNNING
        db.commit()

        adapter = GitHubAdapter()
        projects_discovered = await adapter.search(
            query=query,
            language=language,
            min_stars=min_stars,
            limit=max_results
        )

        projects_saved = 0
        contacts_saved = 0

        for disc_proj in projects_discovered:
            # Check or create Project in db
            existing_proj = db.query(Project).filter(
                Project.organization_id == org_id,
                Project.full_name == disc_proj.full_name
            ).first()

            if not existing_proj:
                existing_proj = Project(
                    id=uuid.uuid4(),
                    organization_id=org_id,
                    name=disc_proj.name,
                    full_name=disc_proj.full_name,
                    description=disc_proj.description,
                    owner=disc_proj.owner,
                    stars_count=disc_proj.stars_count,
                    forks_count=disc_proj.forks_count,
                    language=disc_proj.language,
                    topics=disc_proj.topics,
                    repository_url=disc_proj.repository_url,
                    homepage_url=disc_proj.homepage_url,
                    contributing_url=disc_proj.contributing_url
                )
                db.add(existing_proj)
                db.flush()
                projects_saved += 1
            else:
                existing_proj.stars_count = disc_proj.stars_count
                existing_proj.forks_count = disc_proj.forks_count

            if scan_sources:
                sources = await adapter.fetch_sources(disc_proj)

                # If official website exists and is safe, crawl depth 1
                if disc_proj.homepage_url and "github.com" not in disc_proj.homepage_url:
                    web_adapter = WebsiteAdapter(max_depth=1)
                    web_sources = await web_adapter.crawl_site(disc_proj.homepage_url)
                    sources.extend(web_sources)

                for src in sources:
                    extracted = ContactExtractor.extract_from_text(
                        text=src.content,
                        source_url=src.source_url,
                        source_category=SourceCategory(src.source_category) if src.source_category in SourceCategory.__members__ else SourceCategory.GITHUB_README
                    )

                    for ext_c in extracted:
                        # Check if contact already exists for this organization
                        existing_contact = db.query(Contact).filter(
                            Contact.organization_id == org_id,
                            Contact.email == ext_c.email.lower()
                        ).first()

                        if not existing_contact:
                            # Run verification
                            verif = DNSVerifier.verify_email(ext_c.email, allow_mock=True)

                            existing_contact = Contact(
                                id=uuid.uuid4(),
                                organization_id=org_id,
                                project_id=existing_proj.id,
                                email=ext_c.email.lower(),
                                full_name=ext_c.full_name,
                                role_title=ext_c.role_title,
                                relevance_score=ext_c.relevance_score,
                                verification_status=verif.status,
                                is_suppressed=False
                            )
                            db.add(existing_contact)
                            db.flush()
                            contacts_saved += 1

                            # Add verification record
                            verif_rec = VerificationRecord(
                                id=uuid.uuid4(),
                                contact_id=existing_contact.id,
                                status=verif.status,
                                mx_records=verif.mx_records,
                                details=verif.details,
                                verified_at=datetime.now(timezone.utc)
                            )
                            db.add(verif_rec)

                        # Add provenance source record if not already recorded
                        existing_src = db.query(ContactSource).filter(
                            ContactSource.contact_id == existing_contact.id,
                            ContactSource.source_url == ext_c.source_url
                        ).first()

                        if not existing_src:
                            contact_src = ContactSource(
                                id=uuid.uuid4(),
                                contact_id=existing_contact.id,
                                source_url=ext_c.source_url,
                                source_category=ext_c.source_category,
                                evidence_text=ext_c.evidence_text[:1000],
                                extracted_at=datetime.now(timezone.utc)
                            )
                            db.add(contact_src)

            db.commit()

        job.status = JobStatus.COMPLETED
        job.projects_found = projects_saved
        job.contacts_found = contacts_saved
        db.commit()

        log_audit(
            db,
            action="DISCOVERY_COMPLETED",
            target_type="DISCOVERY_JOB",
            user_id=user_id,
            organization_id=org_id,
            target_id=str(job.id),
            metadata_json={"projects": projects_saved, "contacts": contacts_saved, "query": query}
        )

    except Exception as e:
        db.rollback()
        job = db.query(DiscoveryJob).filter(DiscoveryJob.id == job_id).first()
        if job:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            db.commit()
    finally:
        db.close()


@router.post("/run", response_model=DiscoveryJobOut)
async def trigger_discovery(
    req: DiscoveryQuery,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = DiscoveryJob(
        id=uuid.uuid4(),
        organization_id=current_user.organization_id,
        target_query=req.query,
        job_type="GITHUB_DISCOVERY",
        status=JobStatus.PENDING,
        projects_found=0,
        contacts_found=0
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # In fast synchronous/test execution or background
    await run_discovery_pipeline(
        job_id=job.id,
        org_id=current_user.organization_id,
        user_id=current_user.id,
        query=req.query,
        language=req.language,
        min_stars=req.min_stars,
        max_results=req.max_results,
        scan_sources=req.scan_sources
    )

    db.refresh(job)
    return job


@router.get("/jobs", response_model=List[DiscoveryJobOut])
def list_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    jobs = db.query(DiscoveryJob).filter(
        DiscoveryJob.organization_id == current_user.organization_id
    ).order_by(DiscoveryJob.created_at.desc()).limit(50).all()
    return jobs


@router.get("/jobs/{job_id}", response_model=DiscoveryJobOut)
def get_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(DiscoveryJob).filter(
        DiscoveryJob.id == job_id,
        DiscoveryJob.organization_id == current_user.organization_id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Discovery job not found")
    return job
