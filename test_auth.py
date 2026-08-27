import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("GOOGLE_CLIENT_ID", "dummy")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "dummy")

from src.auth.oauth import hash_token
from src.auth.tenant import set_current_user, get_current_user, current_user_id


def test_token_hash_is_deterministic():
    raw = "some-random-token-value"
    assert hash_token(raw) == hash_token(raw)


def test_token_hash_differs_for_different_tokens():
    assert hash_token("token-a") != hash_token("token-b")


def test_tenant_context_isolation():
    set_current_user("user-123")
    assert get_current_user() == "user-123"

    set_current_user("user-456")
    assert get_current_user() == "user-456"


def test_get_current_user_raises_without_context():
    current_user_id.set(None)
    try:
        get_current_user()
        assert False, "expected PermissionError"
    except PermissionError:
        pass
