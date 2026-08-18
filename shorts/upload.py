from __future__ import annotations

import logging
from pathlib import Path

from shorts.config import CLIENT_SECRETS, TOKEN_PATH
from shorts.copy import (
    description_body,
    missing_required_hashtags,
    parse_hashtags,
    studio_hashtags,
    studio_tags,
    studio_title,
)
from shorts.models import Script, thumb_media_path

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
    parts = [description_body(script.description), studio_hashtags(script)]
    blob = "\n\n".join(p for p in parts if p)
    if disclaimer.strip() and disclaimer.strip() not in blob:
        parts.append(disclaimer.strip())
        blob = "\n\n".join(p for p in parts if p)
    missing = missing_required_hashtags(blob)
    if missing:
        raise ValueError("설명에 주제 해시태그 3개 이상 필요")
    return blob


def studio_meta(script: Script, disclaimer: str) -> dict:
    """Studio에 그대로 붙일 제목·설명·해시태그·태그. 손으로 다시 치지 말 것."""
    hashtags = studio_hashtags(script)
    return {
        "title": studio_title(script.title),
        "description": description_with_disclaimer(script, disclaimer),
        "hashtags": hashtags,
        "hashtag_chips": [item.lstrip("#") for item in parse_hashtags(hashtags)],
        "tags": studio_tags(script),
    }


def upload_video(script: Script, video: Path, cfg: dict) -> str:
    _Request, _Credentials, _Flow, build, MediaFileUpload = _google()
    creds = credentials()
    youtube = build("youtube", "v3", credentials=creds)
    title = studio_title(script.title)
    tags = studio_tags(script)
    desc = description_with_disclaimer(script, cfg.get("disclaimer") or "")
    body = {
        "snippet": {
            "title": title,
            "description": desc,
            "tags": tags,
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
    thumb = thumb_media_path(video.parent)
    if thumb is None:
        raise SystemExit("thumb.png 없음. GenerateImage 16:9 썸네일을 넣어라.")
    youtube.thumbnails().set(
        videoId=video_id,
        media_body=MediaFileUpload(str(thumb), mimetype="image/png", resumable=True),
    ).execute()
    url = "https://youtu.be/%s" % video_id
    log.info("업로드 완료 %s 썸네일 %s", url, thumb.name)
    return video_id
