import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from codesentinel.api.database import SessionLocal, User, get_db
from codesentinel.api.schemas import LoginRequest, TokenResponse

# Environment configuration
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "codesentinel-console-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours
DEFAULT_ADMIN_USER = os.environ.get("DEFAULT_ADMIN_USER", "admin")
DEFAULT_ADMIN_PASSWORD = os.environ.get("DEFAULT_ADMIN_PASSWORD", "admin123")
DEFAULT_MAINTAINER_USER = os.environ.get("DEFAULT_MAINTAINER_USER", "maintainer")
DEFAULT_MAINTAINER_PASSWORD = os.environ.get("DEFAULT_MAINTAINER_PASSWORD", "maintainer123")

PBKDF2_ITERATIONS = 100_000

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)


# --- PBKDF2 Password Hashing ---

def hash_password(password: str) -> str:
    """Hashes a password using PBKDF2-HMAC-SHA256 with a unique random salt."""
    salt = secrets.token_hex(16)
    hash_bytes = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )
    return f"pbkdf2:sha256:{PBKDF2_ITERATIONS}${salt}${hash_bytes.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a stored PBKDF2 hash using constant-time comparison."""
    if not hashed_password or not plain_password:
        return False
    try:
        parts = hashed_password.split("$")
        if len(parts) != 3:
            return False
        meta, salt, expected_hash_hex = parts
        scheme, algo, iterations_str = meta.split(":")
        if scheme != "pbkdf2" or algo != "sha256":
            return False
        iterations = int(iterations_str)
        candidate_bytes = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        )
        return hmac.compare_digest(candidate_bytes.hex(), expected_hash_hex)
    except (ValueError, TypeError):
        return False


# --- JWT (JSON Web Token) Generation & Verification (Pure Standard Library) ---

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(data: str) -> bytes:
    padding = len(data) % 4
    if padding > 0:
        data += "=" * (4 - padding)
    return base64.urlsafe_b64decode(data.encode("utf-8"))


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Creates a signed HS256 JWT access token."""
    to_encode = data.copy()
    now = datetime.now(UTC)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
    })

    header = {"alg": ALGORITHM, "typ": "JWT"}
    header_json = json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_json = json.dumps(to_encode, separators=(",", ":"), sort_keys=True).encode("utf-8")

    header_b64 = _b64url_encode(header_json)
    payload_b64 = _b64url_encode(payload_json)
    signing_input = f"{header_b64}.{payload_b64}".encode()

    signature = hmac.new(SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> dict[str, Any]:
    """Decodes and validates a signed HS256 JWT access token."""
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT format: token must contain 3 segments")

    header_b64, payload_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode()
    expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()

    try:
        actual_sig = _b64url_decode(sig_b64)
    except Exception as err:
        raise ValueError("Invalid JWT signature encoding") from err

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("JWT signature verification failed")

    try:
        payload_bytes = _b64url_decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception as err:
        raise ValueError("Invalid JWT payload") from err

    exp = payload.get("exp")
    if exp is not None:
        now_ts = int(datetime.now(UTC).timestamp())
        if now_ts > exp:
            raise ValueError("JWT token has expired")

    return payload


# --- Default Maintainer User Seeding ---

def seed_default_user(db: Session | None = None) -> None:
    """Seeds default maintainer users on first run if none exists."""
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        # Check if any user exists
        existing_user = db.query(User).first()
        if not existing_user:
            # Seed primary maintainer
            admin_user = User(
                username=DEFAULT_ADMIN_USER,
                hashed_password=hash_password(DEFAULT_ADMIN_PASSWORD),
                role="maintainer",
            )
            db.add(admin_user)

            # Also seed maintainer username if different
            if DEFAULT_MAINTAINER_USER != DEFAULT_ADMIN_USER:
                maintainer_user = User(
                    username=DEFAULT_MAINTAINER_USER,
                    hashed_password=hash_password(DEFAULT_MAINTAINER_PASSWORD),
                    role="maintainer",
                )
                db.add(maintainer_user)

            db.commit()
            print(f"Default maintainer users seeded: '{DEFAULT_ADMIN_USER}', '{DEFAULT_MAINTAINER_USER}'")
    finally:
        if close_session:
            db.close()


# Seed on module import
seed_default_user()


# --- Authentication Dependency ---

def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Dependency that authenticates the Bearer token and returns the current User."""
    token: str | None = None
    if credentials:
        token = credentials.credentials
    else:
        # Fallback check on Authorization header directly
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {e!s}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    username: str | None = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token: missing subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


# --- Authentication API Routes ---

@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate with username and password, returns a signed JWT access token."""
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        data={"sub": user.username, "role": user.role},
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        username=user.username,
        role=user.role,
    )


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """Returns the authenticated user details."""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
    }
