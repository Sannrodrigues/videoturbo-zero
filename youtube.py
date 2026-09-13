"""OAuth and direct YouTube upload helpers for VideoTurbo Zero.

Credentials intentionally live only in Streamlit Secrets. Access tokens stay in
the current browser session and are never written to the repository or disk.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
from typing import Mapping


YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
STATE_TTL_SECONDS = 600


def configured(settings: Mapping[str, str]) -> bool:
    return bool(settings.get("YOUTUBE_CLIENT_ID") and settings.get("YOUTUBE_CLIENT_SECRET") and settings.get("YOUTUBE_REDIRECT_URI"))


def _client_config(settings: Mapping[str, str]) -> dict:
    return {
        "web": {
            "client_id": settings["YOUTUBE_CLIENT_ID"],
            "client_secret": settings["YOUTUBE_CLIENT_SECRET"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings["YOUTUBE_REDIRECT_URI"]],
        }
    }


def _sign(payload: str, client_secret: str) -> str:
    return hmac.new(client_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def _code_verifier(state: str, client_secret: str) -> str:
    """Create a deterministic PKCE verifier that survives the Google redirect."""
    digest = hmac.new(client_secret.encode(), state.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


def make_state(client_secret: str) -> str:
    payload = f"{int(time.time())}.{secrets.token_urlsafe(24)}"
    raw = f"{payload}.{_sign(payload, client_secret)}"
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def valid_state(state: str, client_secret: str) -> bool:
    try:
        padded = state + "=" * (-len(state) % 4)
        payload, signature = base64.urlsafe_b64decode(padded.encode()).decode().rsplit(".", 1)
        issued_at = int(payload.split(".", 1)[0])
    except (ValueError, UnicodeDecodeError):
        return False
    if time.time() - issued_at > STATE_TTL_SECONDS or issued_at > time.time() + 60:
        return False
    return hmac.compare_digest(signature, _sign(payload, client_secret))


def authorization_url(settings: Mapping[str, str]) -> str:
    from google_auth_oauthlib.flow import Flow

    state = make_state(settings["YOUTUBE_CLIENT_SECRET"])
    flow = Flow.from_client_config(
        _client_config(settings), scopes=[YOUTUBE_UPLOAD_SCOPE], redirect_uri=settings["YOUTUBE_REDIRECT_URI"],
        state=state, code_verifier=_code_verifier(state, settings["YOUTUBE_CLIENT_SECRET"]),
    )
    url, _ = flow.authorization_url(
        access_type="offline", include_granted_scopes="true", prompt="consent",
        state=state,
    )
    return url


def credentials_from_code(settings: Mapping[str, str], code: str, state: str):
    if not valid_state(state, settings["YOUTUBE_CLIENT_SECRET"]):
        raise ValueError("A solicitação de conexão expirou. Clique em Conectar YouTube novamente.")
    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_config(
        _client_config(settings), scopes=[YOUTUBE_UPLOAD_SCOPE],
        redirect_uri=settings["YOUTUBE_REDIRECT_URI"], state=state,
        code_verifier=_code_verifier(state, settings["YOUTUBE_CLIENT_SECRET"]),
    )
    flow.fetch_token(code=code)
    return flow.credentials


def upload_video(credentials, video_path: str, title: str, description: str, privacy_status: str) -> str:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    youtube = build("youtube", "v3", credentials=credentials, cache_discovery=False)
    body = {
        "snippet": {
            "title": (title or "Vídeo criado com VideoTurbo Zero")[:100],
            "description": description or "",
            "categoryId": "22",
        },
        "status": {"privacyStatus": privacy_status, "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(video_path, mimetype="video/mp4", chunksize=-1, resumable=True)
    response = youtube.videos().insert(part="snippet,status", body=body, media_body=media).execute()
    return response["id"]
