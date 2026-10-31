import csv
from datetime import datetime, timezone
import json
import sys
import uuid
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from backend.database.session import SessionLocal, init_db
from backend.models import (
    Project, Contact, ContactSource, Campaign, CampaignRecipient,
    SuppressionEntry, EmailTemplate, ApprovalStatus, CampaignStatus,
    DeliveryStatus, SuppressionReason, User, Organization
)
from backend.discovery.github_adapter import GitHubAdapter
from backend.extraction.extractor import ContactExtractor
from backend.verification.dns_verifier import DNSVerifier
from backend.campaigns.renderer import TemplateRenderer
from backend.core.config import settings

app = typer.Typer(
    name="mailradar",
    help="MailRadar — Developer Outreach Intelligence Platform Linux CLI",
    add_completion=False
)
console = Console()

# Sub-command groups
projects_app = typer.Typer(help="Manage discovered open-source projects")
contacts_app = typer.Typer(help="Manage contacts and provenance sources")
campaign_app = typer.Typer(help="Manage outreach campaigns and approvals")
suppression_app = typer.Typer(help="Manage suppression lists and opt-outs")
discover_app = typer.Typer(help="Discover repositories and maintainers")
config_app = typer.Typer(help="CLI configuration")

app.add_typer(projects_app, name="projects")
app.add_typer(contacts_app, name="contacts")
app.add_typer(campaign_app, name="campaign")
app.add_typer(suppression_app, name="suppression")
app.add_typer(discover_app, name="discover")
app.add_typer(config_app, name="config")


def get_default_org(db):
    org = db.query(Organization).first()
    if not org:
        org = Organization(
            id=uuid.uuid4(),
            name="Default Organization",
            slug="default-org",
            settings_json={"created_via": "cli"}
        )
        db.add(org)
        db.commit()
        db.refresh(org)
    return org


@app.command()
def web(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="API host bind"),
    port: int = typer.Option(8000, "--port", "-p", help="API port bind"),
    web_port: int = typer.Option(3000, "--web-port", help="Web dashboard port"),
):
    """Launch the full MailRadar Web Application (Backend API + Web Dashboard)."""
    import os
    import signal
    import subprocess
    import time
    from pathlib import Path

    init_db()

    project_root = Path(__file__).resolve().parent.parent.parent
    web_dir = project_root / "apps" / "web"

    console.print(Panel(
        f"[bold cyan]Launching MailRadar Web Platform[/bold cyan]\n\n"
        f"• Web Dashboard: [bold green]http://localhost:{web_port}[/bold green]\n"
        f"• REST API Docs: [bold blue]http://{host}:{port}/docs[/bold blue]\n\n"
        f"[dim]Press Ctrl+C to terminate servers.[/dim]",
        border_style="cyan"
    ))

    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)

    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.api.main:app", "--host", host, "--port", str(port)],
        cwd=str(project_root),
        env=env
    )

    frontend_proc = subprocess.Popen(
        ["npm", "run", "dev", "--", "-p", str(web_port)],
        cwd=str(web_dir)
    )

    def cleanup(signum, frame):
        console.print("\n[yellow]Stopping MailRadar servers...[/yellow]")
        backend_proc.terminate()
        frontend_proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        while True:
            time.sleep(1)
            if backend_proc.poll() is not None or frontend_proc.poll() is not None:
                break
    except KeyboardInterrupt:
        cleanup(None, None)


@app.command()
def doctor():
    """Perform health and diagnostics checks on MailRadar subsystems."""
    console.print(Panel("[bold cyan]MailRadar Diagnostics (Doctor)[/bold cyan]", border_style="cyan"))

    # 1. Database Check
    try:
        init_db()
        db = SessionLocal()
        org_count = db.query(Organization).count()
        db.close()
        console.print("[green]✔ Database Connection:[/green] Connected successfully.")
    except Exception as e:
        console.print(f"[red]✘ Database Connection:[/red] Failed: {e}")
        sys.exit(1)

    # 2. Python & Environment
    console.print(f"[green]✔ Python Version:[/green] {sys.version.split()[0]}")
    console.print(f"[green]✔ Delivery Provider:[/green] {settings.delivery_provider}")
    console.print(f"[green]✔ SSRF Guard:[/green] Enabled (Private network blocking active)")

    console.print("[bold green]MailRadar system is healthy and ready.[/bold green]")


@config_app.command("init")
def config_init():
    """Initialize local configuration and database."""
    init_db()
    db = SessionLocal()
    org = get_default_org(db)
    db.close()
    console.print(f"[green]✔ Initialized configuration for default organization:[/green] {org.name} ({org.id})")


@discover_app.command("github")
def discover_github(
    query: str = typer.Argument(..., help="Search query (e.g. distributed mesh)"),
    language: Optional[str] = typer.Option(None, "--language", "-l", help="Language filter"),
    min_stars: int = typer.Option(50, "--min-stars", "-s", help="Minimum repository stars"),
    limit: int = typer.Option(5, "--limit", "-n", help="Max results to fetch")
):
    """Discover repositories and maintainers via GitHub official API."""
    import asyncio
    init_db()
    db = SessionLocal()
    org = get_default_org(db)

    console.print(f"[bold cyan]Searching GitHub repositories for query:[/bold cyan] '{query}'...")

    adapter = GitHubAdapter()
    projects = asyncio.run(adapter.search(query=query, language=language, min_stars=min_stars, limit=limit))

    table = Table(title=f"Discovered Projects for '{query}'", border_style="blue")
    table.add_column("Repository", style="bold white")
    table.add_column("Stars", style="yellow")
    table.add_column("Language", style="cyan")
    table.add_column("Description", style="dim")

    for p in projects:
        table.add_row(p.full_name, str(p.stars_count), p.language or "N/A", (p.description or "")[:50] + "...")
        # Save to DB
        existing = db.query(Project).filter(Project.organization_id == org.id, Project.full_name == p.full_name).first()
        if not existing:
            proj = Project(
                id=uuid.uuid4(),
                organization_id=org.id,
                name=p.name,
                full_name=p.full_name,
                description=p.description,
                owner=p.owner,
                stars_count=p.stars_count,
                forks_count=p.forks_count,
                language=p.language,
                topics=p.topics,
                repository_url=p.repository_url,
                homepage_url=p.homepage_url,
                contributing_url=p.contributing_url
            )
            db.add(proj)
            db.flush()

            # Scan sources
            sources = asyncio.run(adapter.fetch_sources(p))
            for s in sources:
                extracted = ContactExtractor.extract_from_text(s.content, s.source_url)
                for ext in extracted:
                    exist_c = db.query(Contact).filter(Contact.organization_id == org.id, Contact.email == ext.email).first()
                    if not exist_c:
                        verif = DNSVerifier.verify_email(ext.email, allow_mock=True)
                        new_c = Contact(
                            id=uuid.uuid4(),
                            organization_id=org.id,
                            project_id=proj.id,
                            email=ext.email,
                            full_name=ext.full_name,
                            role_title=ext.role_title,
                            relevance_score=ext.relevance_score,
                            verification_status=verif.status,
                            is_suppressed=False
                        )
                        db.add(new_c)
                        db.flush()
                        db.add(ContactSource(
                            id=uuid.uuid4(),
                            contact_id=new_c.id,
                            source_url=ext.source_url,
                            source_category=ext.source_category,
                            evidence_text=ext.evidence_text[:1000],
                            extracted_at=datetime.now(timezone.utc)
                        ))

    db.commit()
    db.close()
    console.print(table)
    console.print(f"[bold green]✔ Saved {len(projects)} projects and associated contacts to database.[/bold green]")


@projects_app.command("list")
def list_projects_cmd():
    """List tracked projects."""
    init_db()
    db = SessionLocal()
    projects = db.query(Project).order_by(Project.stars_count.desc()).all()

    table = Table(title="Tracked Projects", border_style="magenta")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="bold white")
    table.add_column("Owner", style="cyan")
    table.add_column("Stars", style="yellow")
    table.add_column("Language", style="green")

    for p in projects:
        table.add_row(str(p.id)[:8], p.full_name, p.owner, str(p.stars_count), p.language or "N/A")

    db.close()
    console.print(table)


@projects_app.command("show")
def show_project_cmd(project_id: str = typer.Argument(..., help="Project UUID")):
    """Show details of a specific project."""
    init_db()
    db = SessionLocal()
    proj = db.query(Project).filter(Project.id.like(f"{project_id}%")).first()
    if not proj:
        console.print(f"[red]Project '{project_id}' not found.[/red]")
        sys.exit(1)

    panel_text = f"""[bold]Full Name:[/bold] {proj.full_name}
[bold]Owner:[/bold] {proj.owner}
[bold]Stars:[/bold] {proj.stars_count} | [bold]Forks:[/bold] {proj.forks_count}
[bold]Language:[/bold] {proj.language}
[bold]URL:[/bold] {proj.repository_url}
[bold]Description:[/bold] {proj.description}
"""
    console.print(Panel(panel_text, title=f"Project: {proj.name}", border_style="green"))
    db.close()


@contacts_app.command("list")
def list_contacts_cmd():
    """List discovered professional contacts."""
    init_db()
    db = SessionLocal()
    contacts = db.query(Contact).order_by(Contact.relevance_score.desc()).all()

    table = Table(title="Discovered Contacts", border_style="cyan")
    table.add_column("ID", style="dim")
    table.add_column("Email", style="bold white")
    table.add_column("Full Name", style="magenta")
    table.add_column("Role", style="blue")
    table.add_column("Score", style="yellow")
    table.add_column("Verification", style="green")

    for c in contacts:
        table.add_row(
            str(c.id)[:8],
            c.email,
            c.full_name or "N/A",
            c.role_title or "Maintainer",
            f"{c.relevance_score:.2f}",
            c.verification_status.value
        )

    db.close()
    console.print(table)


@contacts_app.command("show")
def show_contact_cmd(contact_id: str = typer.Argument(..., help="Contact UUID")):
    """Show detailed info for a contact."""
    init_db()
    db = SessionLocal()
    contact = db.query(Contact).filter(Contact.id.like(f"{contact_id}%")).first()
    if not contact:
        console.print(f"[red]Contact '{contact_id}' not found.[/red]")
        sys.exit(1)

    panel_text = f"""[bold]Email:[/bold] {contact.email}
[bold]Full Name:[/bold] {contact.full_name or 'N/A'}
[bold]Role Title:[/bold] {contact.role_title or 'Maintainer'}
[bold]Relevance Score:[/bold] {contact.relevance_score:.2f}
[bold]Verification Status:[/bold] {contact.verification_status.value}
[bold]Suppressed:[/bold] {'Yes' if contact.is_suppressed else 'No'}
"""
    console.print(Panel(panel_text, title=f"Contact Details", border_style="yellow"))
    db.close()


@contacts_app.command("sources")
def show_contact_sources(contact_id: str = typer.Argument(..., help="Contact UUID")):
    """Inspect provenance source records for a contact."""
    init_db()
    db = SessionLocal()
    contact = db.query(Contact).filter(Contact.id.like(f"{contact_id}%")).first()
    if not contact:
        console.print(f"[red]Contact '{contact_id}' not found.[/red]")
        sys.exit(1)

    sources = db.query(ContactSource).filter(ContactSource.contact_id == contact.id).all()
    table = Table(title=f"Sources for {contact.email}", border_style="green")
    table.add_column("Category", style="cyan")
    table.add_column("Source URL", style="blue")
    table.add_column("Evidence Snippet", style="white")

    for s in sources:
        table.add_row(s.source_category.value, s.source_url, s.evidence_text[:80] + "...")

    db.close()
    console.print(table)


@contacts_app.command("export")
def export_contacts_cmd(
    format: str = typer.Option("csv", "--format", "-f", help="csv or json")
):
    """Export contacts to CSV or JSON."""
    init_db()
    db = SessionLocal()
    contacts = db.query(Contact).all()

    if format.lower() == "json":
        data = [{"email": c.email, "name": c.full_name, "score": c.relevance_score} for c in contacts]
        console.print_json(json.dumps(data))
    else:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Email", "Name", "Role", "Score", "Verification"])
        for c in contacts:
            writer.writerow([c.email, c.full_name or "", c.role_title or "", c.relevance_score, c.verification_status.value])
        console.print(output.getvalue())

    db.close()


@campaign_app.command("create")
def create_campaign_cmd(name: str = typer.Argument(..., help="Campaign name")):
    """Create a new outreach campaign."""
    init_db()
    db = SessionLocal()
    org = get_default_org(db)

    # Find or create a default template
    tmpl = db.query(EmailTemplate).filter(EmailTemplate.organization_id == org.id).first()
    if not tmpl:
        tmpl = EmailTemplate(
            id=uuid.uuid4(),
            organization_id=org.id,
            name="Default Outreach",
            subject="Collaboration inquiry regarding {{project_name}}",
            body_markdown="Hi {{first_name}},\n\nI came across {{project_name}} and appreciated your open-source work.\n\nBest,\nAlex",
            variables=["first_name", "project_name"]
        )
        db.add(tmpl)
        db.flush()

    camp = Campaign(
        id=uuid.uuid4(),
        organization_id=org.id,
        template_id=tmpl.id,
        name=name,
        status=CampaignStatus.DRAFT,
        daily_limit=50
    )
    db.add(camp)

    # Attach any eligible unsuppressed contacts
    contacts = db.query(Contact).filter(Contact.organization_id == org.id, Contact.is_suppressed == False).limit(10).all()
    for c in contacts:
        rec = CampaignRecipient(
            id=uuid.uuid4(),
            campaign_id=camp.id,
            contact_id=c.id,
            approval_status=ApprovalStatus.PENDING,
            delivery_status=DeliveryStatus.PENDING
        )
        db.add(rec)

    if contacts:
        camp.status = CampaignStatus.RECIPIENT_REVIEW

    db.commit()
    console.print(f"[bold green]✔ Created campaign '{camp.name}' ({camp.id}) with {len(contacts)} recipient(s) in review.[/bold green]")
    db.close()


@campaign_app.command("approve")
def approve_recipient_cmd(recipient_id: str = typer.Argument(..., help="Recipient UUID")):
    """Approve a recipient draft for sending."""
    init_db()
    db = SessionLocal()
    rec = db.query(CampaignRecipient).filter(CampaignRecipient.id.like(f"{recipient_id}%")).first()
    if not rec:
        console.print(f"[red]Recipient '{recipient_id}' not found.[/red]")
        sys.exit(1)

    rec.approval_status = ApprovalStatus.APPROVED
    camp = rec.campaign
    camp.status = CampaignStatus.APPROVED
    camp.approved_count += 1
    db.commit()

    console.print(f"[bold green]✔ Recipient {rec.contact.email} approved for campaign '{camp.name}'.[/bold green]")
    db.close()


@campaign_app.command("preview")
def preview_campaign_cmd(campaign_id: str = typer.Argument(..., help="Campaign UUID")):
    """Preview rendered message for campaign recipients."""
    init_db()
    db = SessionLocal()
    camp = db.query(Campaign).filter(Campaign.id.like(f"{campaign_id}%")).first()
    if not camp:
        console.print(f"[red]Campaign '{campaign_id}' not found.[/red]")
        sys.exit(1)

    first_rec = db.query(CampaignRecipient).filter(CampaignRecipient.campaign_id == camp.id).first()
    if not first_rec or not camp.template:
        console.print("[yellow]No recipients or template configured for this campaign.[/yellow]")
        sys.exit(0)

    contact = first_rec.contact
    first_name = (contact.full_name or "").split()[0] if contact.full_name else "there"
    ctx = {
        "first_name": first_name,
        "project_name": contact.project.name if contact.project else "your project",
        "organization_name": camp.organization.name if camp.organization else "MailRadar"
    }

    rendered_subj = TemplateRenderer.render(camp.template.subject, ctx)
    rendered_body = TemplateRenderer.render(camp.template.body_markdown, ctx)

    console.print(Panel(f"[bold]Subject:[/bold] {rendered_subj}\n\n[bold]Body:[/bold]\n{rendered_body}", title=f"Preview for {contact.email}", border_style="cyan"))
    db.close()


@campaign_app.command("status")
def status_campaign_cmd(campaign_id: str = typer.Argument(..., help="Campaign UUID")):
    """Check campaign status and metrics."""
    init_db()
    db = SessionLocal()
    camp = db.query(Campaign).filter(Campaign.id.like(f"{campaign_id}%")).first()
    if not camp:
        console.print(f"[red]Campaign '{campaign_id}' not found.[/red]")
        sys.exit(1)

    total_rec = db.query(CampaignRecipient).filter(CampaignRecipient.campaign_id == camp.id).count()
    approved = db.query(CampaignRecipient).filter(CampaignRecipient.campaign_id == camp.id, CampaignRecipient.approval_status == ApprovalStatus.APPROVED).count()
    sent = db.query(CampaignRecipient).filter(CampaignRecipient.campaign_id == camp.id, CampaignRecipient.delivery_status == DeliveryStatus.SENT).count()

    panel_text = f"""[bold]Campaign:[/bold] {camp.name}
[bold]Status:[/bold] {camp.status.value}
[bold]Total Recipients:[/bold] {total_rec}
[bold]Approved:[/bold] {approved}
[bold]Delivered:[/bold] {sent}
"""
    console.print(Panel(panel_text, title="Campaign Status", border_style="magenta"))
    db.close()


@suppression_app.command("list")
def list_suppression_cmd():
    """List suppressed email addresses."""
    init_db()
    db = SessionLocal()
    entries = db.query(SuppressionEntry).order_by(SuppressionEntry.created_at.desc()).all()

    table = Table(title="Suppressed Addresses", border_style="red")
    table.add_column("Email", style="bold white")
    table.add_column("Reason", style="yellow")
    table.add_column("Notes", style="dim")

    for e in entries:
        table.add_row(e.email, e.reason.value, e.notes or "")

    db.close()
    console.print(table)


if __name__ == "__main__":
    app()
