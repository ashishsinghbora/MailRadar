import uuid
from backend.suppression.checker import SuppressionChecker
from backend.models import SuppressionReason


def test_suppression_global_and_org(db_session, test_organization):
    email = "optout@targetdomain.org"

    # Initially not suppressed
    assert SuppressionChecker.is_suppressed(db_session, email, test_organization.id) is False

    # Add suppression
    entry = SuppressionChecker.suppress_email(
        db=db_session,
        email=email,
        reason=SuppressionReason.OPT_OUT,
        organization_id=test_organization.id,
        notes="Requested unsubscription"
    )
    assert entry is not None

    # Now should be suppressed for this org
    assert SuppressionChecker.is_suppressed(db_session, email, test_organization.id) is True

    # Check case-insensitivity
    assert SuppressionChecker.is_suppressed(db_session, "OPTOUT@targetdomain.org", test_organization.id) is True


def test_unsubscribe_token_lifecycle(test_organization):
    email = "developer@mesh.org"
    token = SuppressionChecker.generate_unsubscribe_token(email, test_organization.id)
    assert token is not None

    payload = SuppressionChecker.decode_unsubscribe_token(token)
    assert payload is not None
    assert payload["email"] == email
    assert payload["org_id"] == str(test_organization.id)
    assert payload["purpose"] == "unsubscribe"
