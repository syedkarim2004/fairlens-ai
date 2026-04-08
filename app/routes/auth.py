"""
FairLens AI — Auth Routes
--------------------------
Google OAuth via Firebase ID token verification.
Issues a local JWT for subsequent API calls.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
import os
import jwt
import datetime

router = APIRouter()
security = HTTPBearer()


# ---------------------------------------------------------------------------
# Firebase Initialization (once)
# ---------------------------------------------------------------------------
def init_firebase():
    if not firebase_admin._apps:
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "./firebase-credentials.json")
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)


init_firebase()

JWT_SECRET = os.getenv("JWT_SECRET", "fairlens-secret-change-in-production")
JWT_ALGORITHM = "HS256"


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------
class GoogleAuthRequest(BaseModel):
    id_token: str


class UserResponse(BaseModel):
    user_id: str
    email: str
    name: str
    photo_url: str
    access_token: str


# In-memory user store (replace with Firestore in production)
user_store: dict = {}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post("/google", response_model=UserResponse)
async def google_auth(request: GoogleAuthRequest):
    """Verify Firebase Google ID token and return JWT."""
    try:
        if firebase_admin._apps:
            decoded = firebase_auth.verify_id_token(request.id_token)
            user_id = decoded["uid"]
            email = decoded.get("email", "")
            name = decoded.get("name", "User")
            photo_url = decoded.get("picture", "")
        else:
            # Dev mode: accept mock token
            import json
            import base64

            parts = request.id_token.split(".")
            if len(parts) >= 2:
                padded = parts[1] + "=" * (-len(parts[1]) % 4)
                payload = json.loads(base64.urlsafe_b64decode(padded))
                user_id = payload.get("sub", "dev-user-123")
                email = payload.get("email", "dev@fairlens.ai")
                name = payload.get("name", "Dev User")
                photo_url = payload.get("picture", "")
            else:
                user_id = "dev-user-123"
                email = "dev@fairlens.ai"
                name = "Dev User"
                photo_url = ""

        # Create JWT
        expire = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        token_payload = {"sub": user_id, "email": email, "name": name, "exp": expire}
        access_token = jwt.encode(token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        # Store user
        user_store[user_id] = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "photo_url": photo_url,
            "audit_count": 0,
        }

        return UserResponse(
            user_id=user_id,
            email=email,
            name=name,
            photo_url=photo_url,
            access_token=access_token,
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Auth failed: {str(e)}")


@router.get("/me")
async def get_me(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Return the current user's profile from the JWT."""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload["sub"]
        user = user_store.get(
            user_id,
            {
                "user_id": user_id,
                "email": payload.get("email"),
                "name": payload.get("name"),
            },
        )
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/demo", response_model=UserResponse)
async def demo_login():
    """Issue a demo JWT — no Firebase required. For development only."""
    user_id = "demo-user-001"
    email = "demo@fairlens.ai"
    name = "Demo User"
    photo_url = ""

    expire = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    token_payload = {"sub": user_id, "email": email, "name": name, "exp": expire}
    access_token = jwt.encode(token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    user_store[user_id] = {
        "user_id": user_id,
        "email": email,
        "name": name,
        "photo_url": photo_url,
        "audit_count": 0,
    }

    return UserResponse(
        user_id=user_id,
        email=email,
        name=name,
        photo_url=photo_url,
        access_token=access_token,
    )


# ---------------------------------------------------------------------------
# Dependency for protected routes
# ---------------------------------------------------------------------------
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency: decode JWT and return payload dict."""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

