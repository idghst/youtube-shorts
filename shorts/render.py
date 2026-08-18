from __future__ import annotations

import logging
import re
import shutil
import subprocess
from pathlib import Path

from shorts.config import ROOT
from shorts.models import Script, Scene, scene_image_path

log = logging.getLogger("shorts")
FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
FONT_FALLBACK = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
LINUX_FONTS = (
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansKR-Regular.otf",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
)
KEYWORD_RE = re.compile(
    r"(\d+(?:\.\d+)?(?:조|억|만|%|퍼센트|년)?|영끌|빚투|주택담보대출|주담대|금리|연체율|가계빚|가계부채|총량)"
)
GOLD = (255, 213, 74, 255)
WHITE = (255, 255, 255, 255)
CAPTION_OVERLAY = "overlay=0:H*2/3-h/2"
CAPTION_MAX_WIDTH_PAD = 80
CAPTION_PAD_Y = 28
CAPTION_LINE_GAP = 8


def require_ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        raise SystemExit("ffmpeg 없음. brew install ffmpeg 후 다시 실행. 렌더를 위조하지 않음.")
    return path


def _run(cmd: list, cwd: Path | None = None) -> None:
    log.info("+ %s", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=str(cwd) if cwd else None)
    except subprocess.CalledProcessError as exc:
        err = (exc.stderr or exc.stdout or "").strip()
        raise SystemExit("ffmpeg 실패:\n%s" % err[-2000:]) from exc


def audio_duration(path: Path) -> float:
    probe = shutil.which("ffprobe") or require_ffmpeg().replace("ffmpeg", "ffprobe")
    out = subprocess.check_output(
        [
            probe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        text=True,
    ).strip()
    try:
        return float(out)
    except ValueError as exc:
        raise SystemExit("오디오 길이 읽기 실패: %s" % out) from exc


def resolve_bgm(cfg: dict) -> Path:
    raw = str(cfg.get("bgm") or "assets/bgm/valley-sunset.mp3")
    path = Path(raw)
    if not path.is_absolute():
        path = ROOT / path
    if not path.is_file() or path.stat().st_size == 0:
        raise SystemExit("BGM 없음: %s. assets/bgm/ 에 Mixkit/Pixabay/CC0 트랙을 넣어라." % path)
    return path


def _split_captions(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?。])\s+", text.replace("\n", " ").strip())
    parts = [p.strip() for p in parts if p.strip()]
    return parts or [text.strip()]


def caption_beats(scene: Scene) -> list[tuple[str, float]]:
    texts = [c.strip() for c in (scene.captions or []) if str(c).strip()]
    if not texts:
        texts = _split_captions(scene.text)
    n = len(texts)
    slot = scene.duration / n
    beats = []
    elapsed = 0.0
    for i, text in enumerate(texts):
        dur = scene.duration - elapsed if i == n - 1 else slot
        beats.append((text, dur))
        elapsed += dur
    return beats


def _caption_font(size: int):
    try:
        from PIL import ImageFont
    except ImportError as exc:
        raise SystemExit("자막용 Pillow 필요. pip install -r requirements.txt") from exc
    for candidate in (FONT, FONT_FALLBACK, *LINUX_FONTS):
        if not Path(candidate).is_file():
            continue
        for index in (1, 2, 0):
            try:
                return ImageFont.truetype(candidate, size, index=index)
            except OSError:
                continue
            except TypeError:
                try:
                    return ImageFont.truetype(candidate, size)
                except OSError:
                    break
    raise SystemExit("한글 폰트 없음")


def _line_width(draw, line: str, font) -> tuple[int, int]:
    tokens = [p for p in KEYWORD_RE.split(line) if p]
    if not tokens:
        tokens = [line]
    w = 0
    h = 0
    for tok in tokens:
        bbox = draw.textbbox((0, 0), tok, font=font, stroke_width=5)
        w += bbox[2] - bbox[0]
        h = max(h, bbox[3] - bbox[1])
    return w, h


def wrap_caption(text: str, width: int = 1080) -> list[str]:
    from PIL import Image, ImageDraw

    raw = (text or "").replace("\n", " ").strip() or " "
    font = _caption_font(76)
    probe = Image.new("RGBA", (width, 10), (0, 0, 0, 0))
    draw = ImageDraw.Draw(probe)
    max_w = max(width - CAPTION_MAX_WIDTH_PAD, 200)
    if _line_width(draw, raw, font)[0] <= max_w:
        return [raw]
    lines: list[str] = []
    rest = raw
    while rest and len(lines) < 2:
        lo, hi = 1, len(rest)
        best = 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if _line_width(draw, rest[:mid], font)[0] <= max_w:
                best = mid
                lo = mid + 1
            else:
                hi = mid - 1
        chunk = rest[:best].rstrip() or rest[:best]
        rest = rest[len(chunk) :].lstrip()
        if len(lines) == 1 and rest:
            chunk = (chunk + rest).strip()
            rest = ""
        lines.append(chunk)
    return lines or [raw]


def write_caption_png(text: str, path: Path, width: int = 1080) -> None:
    from PIL import Image, ImageDraw

    lines = wrap_caption(text, width=width)
    font = _caption_font(76)
    canvas = Image.new("RGBA", (width, 420), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    sizes = [_line_width(draw, line, font) for line in lines]
    y = 40
    for line, (_lw, lh) in zip(lines, sizes):
        tokens = [p for p in KEYWORD_RE.split(line) if p] or [line]
        tw, _ = _line_width(draw, line, font)
        x = (width - tw) // 2
        for tok in tokens:
            fill = GOLD if KEYWORD_RE.fullmatch(tok) else WHITE
            draw.text((x, y), tok, font=font, fill=fill, stroke_width=5, stroke_fill=(0, 0, 0, 240))
            bbox = draw.textbbox((x, y), tok, font=font, stroke_width=5)
            x = bbox[2]
        y += lh + CAPTION_LINE_GAP
    ink_box = canvas.getbbox()
    if ink_box is None:
        bar = Image.new("RGBA", (width, 96), (0, 0, 0, 255))
        bar.save(path)
        return
    ink = canvas.crop(ink_box)
    bar_h = ink.size[1] + CAPTION_PAD_Y * 2
    bar = Image.new("RGBA", (width, bar_h), (0, 0, 0, 255))
    bar.paste(ink, ((width - ink.size[0]) // 2, CAPTION_PAD_Y), ink)
    bar.save(path)


def _ken_burns(ffmpeg: str, image: Path, dest: Path, seconds: float, fps: int, w: int, h: int) -> None:
    frames = max(int(round(seconds * fps)), fps)
    vf = (
        "scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,"
        "zoompan=z='min(zoom+0.0012,1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        ":d=%d:s=%dx%d:fps=%d"
        % (w + 80, h + 140, w + 80, h + 140, frames, w, h, fps)
    )
    _run(
        [
            ffmpeg,
            "-y",
            "-loop",
            "1",
            "-i",
            str(image),
            "-vf",
            vf,
            "-t",
            "%.3f" % seconds,
            "-r",
            str(fps),
            "-pix_fmt",
            "yuv420p",
            "-an",
            str(dest),
        ]
    )


def _mix_bgm(ffmpeg: str, silent: Path, bgm: Path, dest: Path, duration: float, volume: float) -> None:
    src_dur = audio_duration(bgm)
    loop = ["-stream_loop", "-1"] if src_dur + 0.05 < duration else []
    fade = min(3.0, max(1.8, duration * 0.06))
    fade_st = max(duration - fade, 0)
    af = "volume=%.3f,afade=t=in:st=0:d=0.4,afade=t=out:st=%.3f:d=%.3f" % (volume, fade_st, fade)
    _run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(silent),
            *loop,
            "-i",
            str(bgm),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-filter:a",
            af,
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-shortest",
            "-t",
            "%.3f" % duration,
            str(dest),
        ]
    )


def render_job(script: Script, job_dir: Path, cfg: dict) -> Path:
    ffmpeg = require_ffmpeg()
    width = int(cfg.get("width") or 1080)
    height = int(cfg.get("height") or 1920)
    fps = int(cfg.get("fps") or 30)
    duration = script.total_duration()
    if not (50 <= duration <= 60):
        raise SystemExit("장면 duration 합은 50~60초 (지금 %.1f)" % duration)
    bgm = resolve_bgm(cfg)
    volume = float(cfg.get("bgm_volume") or 0.32)

    missing = []
    images = []
    for i, _scene in enumerate(script.scenes, 1):
        image = scene_image_path(job_dir, i)
        if not image.is_file():
            missing.append(image.name)
        else:
            images.append(image)
    if missing:
        raise SystemExit(
            "장면 이미지 없음: %s. Cursor GenerateImage 로 scene-01.png … 를 이 폴더에 넣어라."
            % ", ".join(missing)
        )

    work = job_dir / "work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir()
    clips = []
    for i, (image, scene) in enumerate(zip(images, script.scenes), 1):
        raw = work / ("clip-%02d-raw.mp4" % i)
        _ken_burns(ffmpeg, image, raw, scene.duration, fps, width, height)
        elapsed = 0.0
        for j, (text, beat_dur) in enumerate(caption_beats(scene), 1):
            cap = work / ("cap-%02d-%02d.png" % (i, j))
            write_caption_png(text, cap, width=width)
            clip = work / ("clip-%02d-%02d.mp4" % (i, j))
            _run(
                [
                    ffmpeg,
                    "-y",
                    "-ss",
                    "%.3f" % elapsed,
                    "-t",
                    "%.3f" % beat_dur,
                    "-i",
                    str(raw),
                    "-i",
                    str(cap),
                    "-filter_complex",
                    CAPTION_OVERLAY,
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    "-an",
                    "-t",
                    "%.3f" % beat_dur,
                    str(clip),
                ]
            )
            clips.append(clip)
            elapsed += beat_dur

    concat = work / "concat.txt"
    concat.write_text("".join("file '%s'\n" % c.resolve() for c in clips), encoding="utf-8")
    silent = work / "video-silent.mp4"
    _run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", "-an", str(silent)])
    video = job_dir / "video.mp4"
    _mix_bgm(ffmpeg, silent, bgm, video, duration, volume)
    if not video.is_file() or video.stat().st_size == 0:
        raise SystemExit("video.mp4 생성 실패")
    log.info("렌더 완료 %s (%.1fs, BGM)", video, duration)
    return video
