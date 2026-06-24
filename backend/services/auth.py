import logging
import secrets
import hashlib
from typing import Optional
from datetime import timedelta

import bcrypt
from fastapi import Request

from database import get_db, utcnow
from models import User, AuthSession, PremiumUnlock

logger = logging.getLogger(__name__)

# bcrypt only ever uses the first 72 bytes of a password and, as of bcrypt 5.0,
# raises ValueError when handed more rather than silently truncating. We truncate
# to that boundary ourselves so a long passphrase (e.g. from a password manager)
# hashes and verifies consistently instead of crashing the endpoint with a 500.
# This matches bcrypt's own guidance and its pre-5.0 behaviour, so every existing
# stored hash (all created from <=72-byte inputs) keeps verifying unchanged.
BCRYPT_MAX_BYTES = 72


def _password_bytes(password: str) -> bytes:
    """Encode a password to the byte slice bcrypt will actually consume."""
    return password.encode('utf-8')[:BCRYPT_MAX_BYTES]


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(_password_bytes(password), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash. Never raises: a malformed or empty
    stored hash is treated as a non-match (fail closed) rather than a 500."""
    try:
        return bcrypt.checkpw(_password_bytes(password), password_hash.encode('utf-8'))
    except (ValueError, TypeError):
        return False


def generate_session_token() -> str:
    """Generate a secure random session token"""
    return secrets.token_urlsafe(32)


# A bcrypt hash of a random throwaway secret, computed lazily on first use (like
# get_client() in services/llm.py) so importing this module has no bcrypt side
# effect. login() verifies the submitted password against this whenever the email
# is unknown, so a missing account costs the same bcrypt work as a wrong password.
# Without it, "no such user" would return without hashing at all, and the timing
# gap would let an attacker enumerate which emails are registered.
_dummy_password_hash = None


def dummy_verify(password: str) -> bool:
    """Run a bcrypt comparison against a throwaway hash. Always returns False;
    exists only to equalise login response timing for non-existent accounts."""
    global _dummy_password_hash
    if _dummy_password_hash is None:
        _dummy_password_hash = hash_password(secrets.token_urlsafe(32))
    return verify_password(password, _dummy_password_hash)


def hash_document(text: str) -> str:
    """Create a hash of document text for tracking premium unlocks"""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def create_user(email: str, password: str) -> Optional[User]:
    """Create a new user"""
    db = get_db()
    if db is None:
        return None

    try:
        user = User(
            email=email.lower().strip(),
            password_hash=hash_password(password)
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        logger.error("Error creating user: %s", e)
        db.rollback()
        return None
    finally:
        db.close()


def get_user_by_email(email: str) -> Optional[User]:
    """Get a user by email"""
    db = get_db()
    if db is None:
        return None

    try:
        user = db.query(User).filter(User.email == email.lower().strip()).first()
        return user
    except Exception as e:
        logger.error("Error getting user: %s", e)
        return None
    finally:
        db.close()


def create_session(user_id: int) -> Optional[str]:
    """Create a new auth session and return the token"""
    db = get_db()
    if db is None:
        return None

    try:
        token = generate_session_token()
        session = AuthSession(
            user_id=user_id,
            token=token,
            expires_at=utcnow() + timedelta(days=30)
        )
        db.add(session)
        db.commit()
        return token
    except Exception as e:
        logger.error("Error creating session: %s", e)
        db.rollback()
        return None
    finally:
        db.close()


def get_user_from_token(token: str) -> Optional[User]:
    """Get user from session token"""
    if not token:
        return None

    db = get_db()
    if db is None:
        return None

    try:
        session = db.query(AuthSession).filter(
            AuthSession.token == token,
            AuthSession.expires_at > utcnow()
        ).first()
        if session:
            return db.query(User).filter(User.id == session.user_id).first()
        return None
    except Exception as e:
        logger.error("Error getting user from token: %s", e)
        return None
    finally:
        db.close()


def delete_session(token: str) -> bool:
    """Delete a session (logout)"""
    db = get_db()
    if db is None:
        return False

    try:
        db.query(AuthSession).filter(AuthSession.token == token).delete()
        db.commit()
        return True
    except Exception as e:
        logger.error("Error deleting session: %s", e)
        db.rollback()
        return False
    finally:
        db.close()


def add_credits_to_user(user_id: int, credits: int) -> bool:
    """Add credits to a user account"""
    db = get_db()
    if db is None:
        return False

    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.credits += credits
            db.commit()
            return True
        return False
    except Exception as e:
        logger.error("Error adding credits: %s", e)
        db.rollback()
        return False
    finally:
        db.close()


def use_credit(user_id: int, document_hash: str) -> bool:
    """Use a credit to unlock a document. Returns True if successful."""
    db = get_db()
    if db is None:
        return False

    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or user.credits < 1:
            return False

        # Check if already unlocked
        existing = db.query(PremiumUnlock).filter(
            PremiumUnlock.user_id == user_id,
            PremiumUnlock.document_hash == document_hash
        ).first()
        if existing:
            return True  # Already unlocked, no credit needed

        # Deduct credit and record unlock
        user.credits -= 1
        unlock = PremiumUnlock(user_id=user_id, document_hash=document_hash)
        db.add(unlock)
        db.commit()
        return True
    except Exception as e:
        logger.error("Error using credit: %s", e)
        db.rollback()
        return False
    finally:
        db.close()


def check_premium_access(user_id: int, document_hash: str) -> bool:
    """Check if user has premium access to a document"""
    db = get_db()
    if db is None:
        return False

    try:
        unlock = db.query(PremiumUnlock).filter(
            PremiumUnlock.user_id == user_id,
            PremiumUnlock.document_hash == document_hash
        ).first()
        return unlock is not None
    except Exception as e:
        logger.error("Error checking premium access: %s", e)
        return False
    finally:
        db.close()


def get_session_token(request: Request) -> Optional[str]:
    """Resolve the session token a request is carrying.

    The SPA authenticates with an ``Authorization: Bearer`` header (the token is
    kept in localStorage); login/signup also set the same token as an httponly
    cookie, which the browser sends automatically on same-origin requests. Prefer
    the header and fall back to the cookie so every auth-aware endpoint — both
    ``get_current_user`` (read) and ``logout`` (revoke) — treats the two
    credentials identically. Returns None when neither is present.
    """
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]
    return request.cookies.get("auth_token")


def get_current_user(request: Request) -> Optional[User]:
    """Extract current user from auth header or cookie"""
    token = get_session_token(request)
    return get_user_from_token(token) if token else None
