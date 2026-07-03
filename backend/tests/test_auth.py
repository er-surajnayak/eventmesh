"""JWT verification tests (Supabase JWKS / ES256 path).

We mint ES256 tokens with a local EC keypair and stub the JWKS client to return
its public key, so the full verify path is exercised without a live Supabase.
"""

import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.security import HTTPAuthorizationCredentials

from app.core import security
from app.core.config import settings
from app.core.exceptions import UnauthorizedError


@pytest.fixture
def es256_keypair():
    return ec.generate_private_key(ec.SECP256R1())


@pytest.fixture(autouse=True)
def stub_jwks(monkeypatch, es256_keypair):
    # Ensure the JWKS path is taken, and return our public key as the signing key.
    monkeypatch.setattr(settings, "supabase_jwks_url", "https://example.test/jwks")

    class _Key:
        def __init__(self, key):
            self.key = key

    class _Client:
        def get_signing_key_from_jwt(self, _token):
            return _Key(es256_keypair.public_key())

    monkeypatch.setattr(security, "_get_jwks_client", lambda: _Client())


def _token(priv, **claims) -> str:
    payload = {
        "sub": "user-123",
        "email": "user@example.com",
        "aud": "authenticated",
        "exp": int(time.time()) + 300,
        **claims,
    }
    return jwt.encode(payload, priv, algorithm="ES256")


def _creds(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


async def test_valid_token_accepted(es256_keypair):
    user = await security.get_current_user(_creds(_token(es256_keypair)))
    assert user.id == "user-123"
    assert user.email == "user@example.com"


async def test_missing_token_rejected():
    with pytest.raises(UnauthorizedError):
        await security.get_current_user(None)


async def test_expired_token_rejected(es256_keypair):
    token = _token(es256_keypair, exp=int(time.time()) - 10)
    with pytest.raises(UnauthorizedError):
        await security.get_current_user(_creds(token))


async def test_wrong_audience_rejected(es256_keypair):
    token = _token(es256_keypair, aud="some-other-service")
    with pytest.raises(UnauthorizedError):
        await security.get_current_user(_creds(token))


async def test_missing_sub_rejected(es256_keypair):
    # `sub` is required; drop it by signing a payload without it.
    payload = {"aud": "authenticated", "exp": int(time.time()) + 300}
    token = jwt.encode(payload, es256_keypair, algorithm="ES256")
    with pytest.raises(UnauthorizedError):
        await security.get_current_user(_creds(token))


async def test_tampered_signature_rejected(es256_keypair):
    other = ec.generate_private_key(ec.SECP256R1())
    token = _token(other)  # signed by a different key than the JWKS returns
    with pytest.raises(UnauthorizedError):
        await security.get_current_user(_creds(token))
