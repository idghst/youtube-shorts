from __future__ import annotations

import json
import logging
from pathlib import Path

from shorts.config import (
    DEFAULT_CHANNEL,
    OUT_DIR,
    auto_publish,
    channel_dir,
    channel_from_job,
    ensure_dirs,
    load_config,
    youtube_channel_id,
)
from shorts.models import load_headline, load_script, scene_image_path
from shorts.news import pick_job
from shorts.render import render_job, require_ffmpeg
from shorts.store import mark_used

log = logging.getLogger("shorts")


def latest_open_job(out_dir: Path = OUT_DIR, channel: str | None = None) -> Path | None:
    if channel:
        roots = [channel_dir(channel)]
    elif out_dir.is_dir():
        roots = [p for p in out_dir.iterdir() if p.is_dir()]
    else:
        return None
    jobs = []
    for root in roots:
        if not root.is_dir():
            continue
        for job in root.iterdir():
            if job.is_dir() and (job / "headline.json").is_file() and not (job / "video.mp4").is_file():
                jobs.append(job)
    if not jobs:
        return None
    jobs.sort(key=lambda p: p.name, reverse=True)
    return jobs[0]


def resolve_job(
    dir_arg: str | None,
    cfg: dict,
    pick_if_needed: bool,
    channel: str | None = None,
) -> Path:
    if dir_arg:
        job = Path(dir_arg).expanduser().resolve()
        if not job.is_dir():
            raise SystemExit("잡 폴더 없음: %s" % job)
        return job
    open_job = latest_open_job(channel=channel)
    if open_job:
        return open_job
    if not pick_if_needed:
        raise SystemExit("진행 중 잡 없음. 먼저 python -m shorts pick --channel %s" % (channel or DEFAULT_CHANNEL))
    job = pick_job(cfg, channel or DEFAULT_CHANNEL)
    headline = load_headline(job / "headline.json")
    log.info("헤드라인 [%s] %s", headline.source, headline.title)
    log.info("잡 %s", job)
    return job


def missing_agent_assets(job: Path) -> list:
    missing = []
    if not (job / "script.json").is_file():
        missing.append("script.json (에이전트가 대본 작성)")
        return missing
    try:
        script = load_script(job / "script.json")
    except ValueError as exc:
        missing.append("script.json 오류: %s" % exc)
        return missing
    for i, _scene in enumerate(script.scenes, 1):
        path = scene_image_path(job, i)
        if not path.is_file():
            missing.append("%s (GenerateImage)" % path.name)
    return missing


def record_job(
    job: Path,
    status: str,
    *,
    cfg: dict | None = None,
    video_path: str = "",
    video_id: str = "",
) -> None:
    data = cfg if cfg is not None else load_config()
    headline = load_headline(job / "headline.json")
    channel = channel_from_job(job)
    mark_used(
        headline,
        status=status,
        channel=channel,
        video_path=video_path,
        video_id=video_id,
        job_path=str(job),
        youtube_channel_id=youtube_channel_id(data, channel),
        cfg=data,
    )


def cmd_pick(channel: str = DEFAULT_CHANNEL) -> Path:
    cfg = load_config()
    ensure_dirs()
    job = pick_job(cfg, channel)
    headline = load_headline(job / "headline.json")
    log.info("헤드라인 [%s] %s", headline.source, headline.title)
    print(job)
    return job


def cmd_render(dir_arg: str | None) -> Path:
    cfg = load_config()
    require_ffmpeg()
    job = resolve_job(dir_arg, cfg, pick_if_needed=False)
    gaps = missing_agent_assets(job)
    if gaps:
        raise SystemExit("렌더 전 필요:\n- " + "\n- ".join(gaps))
    script = load_script(job / "script.json")
    video = render_job(script, job, cfg)
    record_job(job, "rendered", cfg=cfg, video_path=str(video))
    print(video)
    return video


def cmd_upload(dir_arg: str | None, dry_run: bool) -> None:
    cfg = load_config()
    job = resolve_job(dir_arg, cfg, pick_if_needed=False)
    video = job / "video.mp4"
    if not video.is_file():
        raise SystemExit("video.mp4 없음. 먼저 render")
    if dry_run or not auto_publish():
        log.info("업로드 건너뜀 (dry-run 또는 AUTO_PUBLISH=0). %s", video)
        print(video)
        return
    from shorts.upload import upload_video

    script = load_script(job / "script.json")
    video_id = upload_video(script, video, cfg)
    record_job(job, "uploaded", cfg=cfg, video_path=str(video), video_id=video_id)
    print("https://youtu.be/%s" % video_id)


def cmd_record(dir_arg: str, status: str, video_id: str = "") -> None:
    job = Path(dir_arg).expanduser().resolve()
    if not job.is_dir() or not (job / "headline.json").is_file():
        raise SystemExit("잡 폴더/headline.json 없음: %s" % job)
    if status == "uploaded" and not video_id:
        raise SystemExit("uploaded 는 --video-id 필요")
    video = job / "video.mp4"
    record_job(
        job,
        status,
        video_path=str(video) if video.is_file() else "",
        video_id=video_id,
    )
    print("%s %s %s" % (status, channel_from_job(job), video_id or job))


def cmd_run(dir_arg: str | None, dry_run: bool, channel: str | None = None) -> None:
    cfg = load_config()
    ensure_dirs()
    require_ffmpeg()
    job = resolve_job(dir_arg, cfg, pick_if_needed=True, channel=channel)
    gaps = missing_agent_assets(job)
    if gaps:
        hint = {
            "job": str(job),
            "headline": str(job / "headline.json"),
            "need": gaps,
            "next": [
                "에이전트가 script.json 작성 (외부 LLM API 금지)",
                "GenerateImage 로 scene-01.png … 저장",
                "python -m shorts run --dry-run --dir %s" % job,
            ],
        }
        print(json.dumps(hint, ensure_ascii=False, indent=2))
        raise SystemExit("에이전트 단계가 남음. 위 JSON 참고.")
    script = load_script(job / "script.json")
    video = render_job(script, job, cfg)
    record_job(job, "rendered", cfg=cfg, video_path=str(video))
    log.info("로컬 산출 %s + %s", video, job / "script.json")
    if dry_run or not auto_publish():
        log.info("YouTube 건너뜀 (dry-run 또는 AUTO_PUBLISH=0)")
        print(video)
        return
    from shorts.upload import upload_video

    video_id = upload_video(script, video, cfg)
    record_job(job, "uploaded", cfg=cfg, video_path=str(video), video_id=video_id)
    print("https://youtu.be/%s" % video_id)
