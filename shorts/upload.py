from __future__ import annotations

import logging
from pathlib import Path

from shorts.config import CLIENT_SECRETS, TOKEN_PATH
from shorts.copy import description_body, studio_title
from shorts.models import Script

log = logging.getLogger("shorts")
SCOPE = ["https://www.googleapis.com/auth/youtube.upload"]


def _google():
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError as exc:
        raise SystemExit(
            "YouTube 라이브러리 필요. pip install -r requirements.txt"
        ) from exc
    return Request, Credentials, InstalledAppFlow, build, MediaFileUpload


def credentials():
    Request, Credentials, InstalledAppFlow, _build, _media = _google()
    creds = None
    if TOKEN_PATH.is_file():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPE)
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
        return creds
    if not CLIENT_SECRETS.is_file():
        raise SystemExit(
            "client_secrets.json 없음. Google Cloud Desktop OAuth JSON 을 저장소 루트에 둬라."
        )
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS), SCOPE)
    creds = flow.run_local_server(port=0)
    TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    log.info("OAuth 토큰 저장 %s", TOKEN_PATH)
    return creds


def auth() -> None:
    credentials()
    log.info("YouTube OAuth 완료")


def description_with_disclaimer(script: Script, disclaimer: str) -> str:
    parts = [description_body(script.description)]
    blob = "\n".join(p for p in parts if p)
    if script.hashtags and script.hashtags not in blob:
        parts.append(script.hashtags)
        blob = "\n".join(p for p in parts if p)
    if "#Shorts" not in blob and "#shorts" not in blob:
        parts.append("#shorts")
    if disclaimer.strip() and disclaimer.strip() not in blob:
        parts.append(disclaimer.strip())
    return "\n\n".join(p for p in parts if p)


def upload_video(script: Script, video: Path, cfg: dict) -> str:
    _Request, _Credentials, _Flow, build, MediaFileUpload = _google()
    creds = credentials()
    youtube = build("youtube", "v3", credentials=creds)
    title = studio_title(script.title)
    tags = list(script.tags)
    for extra in ("쇼츠", "재테크", "경제"):
        if extra not in tags:
            tags.append(extra)
    body = {
        "snippet": {
            "title": title,
            "description": description_with_disclaimer(script, cfg.get("disclaimer") or ""),
            "tags": tags[:20],
            "categoryId": str(cfg.get("youtube_category_id") or "22"),
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(str(video), mimetype="video/mp4", resumable=True)
    log.info("YouTube 업로드 시작: %s", title)
    resp = (
        youtube.videos()
        .insert(part="snippet,status", body=body, media_body=media)
        .execute()
    )
    video_id = resp.get("id") or ""
    if not video_id:
        raise SystemExit("업로드 응답에 id 없음")
    url = "https://youtu.be/%s" % video_id
    log.info("업로드 완료 %s", url)
    return video_id
