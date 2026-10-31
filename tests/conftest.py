import os
import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Use an isolated test database
os.environ["DATABASE_URL"] = "sqlite:///./test_mailradar.db"
os.environ["DELIVERY_PROVIDER"] = "sandbox"

from backend.database.base import Base
from backend.database.session import engine, SessionLocal, get_db
from backend.models import User, Organization, UserRole, Project, Contact, SourceCategory
from backend.core.security import hash_password, create_access_token
from backend.api.main import app


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_mailradar.db"):
        os.remove("./test_mailradar.db")


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_organization(db_session):
    org = db_session.query(Organization).filter(Organization.slug == "test-org").first()
    if not org:
        org = Organization(
            id=uuid.uuid4(),
            name="Test Intelligence Org",
            slug="test-org",
            settings_json={"mode": "test"}
        )
        db_session.add(org)
        db_session.commit()
        db_session.refresh(org)
    return org


@pytest.fixture
def test_user(db_session, test_organization):
    user = db_session.query(User).filter(User.email == "tester@mailradar.dev").first()
    if not user:
        user = User(
            id=uuid.uuid4(),
            email="tester@mailradar.dev",
            hashed_password=hash_password("SuperSecretPass123!"),
            full_name="Test Operator",
            role=UserRole.ADMIN,
            is_active=True,
            organization_id=test_organization.id
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user, test_organization):
    token = create_access_token(
        subject=test_user.id,
        claims={
            "role": test_user.role.value,
            "organization_id": str(test_organization.id),
            "email": test_user.email
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client():
    return TestClient(app)
