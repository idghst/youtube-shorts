from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class Headline:
    source: str
    title: str
    summary: str
    link: str
    published: str
    hash: str

    def to_json(self) -> dict:
        return asdict(self)

    @classmethod
    def from_json(cls, data: dict) -> "Headline":
        return cls(
            source=str(data["source"]),
            title=str(data["title"]),
            summary=str(data.get("summary") or ""),
            link=str(data.get("link") or ""),
            published=str(data.get("published") or ""),
            hash=str(data["hash"]),
        )


BEAT_SEC = 3.0
ANATOMY_LOCK = "exactly two hands and two feet, no extra limbs"


@dataclass
class Style:
    anchor: str
    mood: str = ""
    face: str = ""
    wardrobe: str = ""

    def to_json(self) -> dict:
        data = {"anchor": self.anchor}
        if self.face:
            data["face"] = self.face
        if self.wardrobe:
            data["wardrobe"] = self.wardrobe
        if self.mood:
            data["mood"] = self.mood
        return data


@dataclass
class Beat:
    image_prompt: str


@dataclass
class Scene:
    text: str
    image_prompt: str = ""
    duration: float = 0
    captions: list = field(default_factory=list)
    beats: list = field(default_factory=list)


@dataclass
class Script:
    title: str
    description: str
    tags: list = field(default_factory=list)
    hashtags: str = ""
    scenes: list = field(default_factory=list)
    style: Style | None = None

    def total_duration(self) -> float:
        return sum(s.duration for s in self.scenes)

    def all_beats(self) -> list:
        out = []
        for s in self.scenes:
            out.extend(s.beats)
        return out

    def to_json(self) -> dict:
        scenes = []
        for s in self.scenes:
            item = {
                "text": s.text,
                "duration": s.duration,
                "beats": [{"image_prompt": b.image_prompt} for b in s.beats],
            }
            if s.captions:
                item["captions"] = list(s.captions)
            if s.image_prompt and not s.beats:
                item["image_prompt"] = s.image_prompt
            scenes.append(item)
        data = {
            "title": self.title,
            "description": self.description,
            "tags": list(self.tags),
            "scenes": scenes,
        }
        if self.hashtags:
            data["hashtags"] = self.hashtags
        if self.style and self.style.anchor:
            data["style"] = self.style.to_json()
        return data


def load_headline(path: Path) -> Headline:
    return Headline.from_json(json.loads(path.read_text(encoding="utf-8")))


def load_script(path: Path) -> Script:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("script.json 은 객체여야 함")
    scenes = []
    for i, raw in enumerate(data.get("scenes") or [], 1):
        text = str(raw.get("text") or "").strip()
        try:
            duration = float(raw.get("duration"))
        except (TypeError, ValueError):
            raise ValueError("scenes[%d] 에 duration(초) 필요" % i)
        if duration <= 0:
            raise ValueError("scenes[%d] duration 은 0보다 커야 함" % i)
        if not text:
            raise ValueError("scenes[%d] 에 text 필요" % i)
        nbeat = int(round(duration / BEAT_SEC))
        if abs(duration - nbeat * BEAT_SEC) > 0.01:
            raise ValueError("scenes[%d] duration 은 3초 배수" % i)
        raw_beats = raw.get("beats")
        if not raw_beats:
            raise ValueError("scenes[%d] 에 beats 필요" % i)
        if not isinstance(raw_beats, list):
            raise ValueError("scenes[%d] beats 는 배열" % i)
        if len(raw_beats) != nbeat:
            raise ValueError("scenes[%d] beats 는 %d개 (3초당 1장)" % (i, nbeat))
        beats = []
        for j, item in enumerate(raw_beats, 1):
            if isinstance(item, str):
                prompt = item.strip()
            elif isinstance(item, dict):
                prompt = str(item.get("image_prompt") or "").strip()
            else:
                raise ValueError("scenes[%d].beats[%d] 형식 오류" % (i, j))
            if not prompt:
                raise ValueError("scenes[%d].beats[%d] image_prompt 필요" % (i, j))
            beats.append(Beat(image_prompt=prompt))
        raw_caps = raw.get("captions") or []
        if raw_caps and not isinstance(raw_caps, list):
            raise ValueError("scenes[%d] captions 는 배열" % i)
        captions = [str(c).strip() for c in raw_caps if str(c).strip()]
        scenes.append(Scene(text=text, duration=duration, captions=captions, beats=beats))
    title = str(data.get("title") or "").strip()
    if not title:
        raise ValueError("title 필요")
    if not scenes:
        raise ValueError("scenes 가 비어 있음")
    if not (4 <= len(scenes) <= 5):
        raise ValueError("scenes 는 4~5개")
    total = sum(s.duration for s in scenes)
    nbeat = sum(len(s.beats) for s in scenes)
    if not (48 <= total <= 60):
        raise ValueError("장면 duration 합은 48~60초 (지금 %.1f)" % total)
    if not (16 <= nbeat <= 20):
        raise ValueError("이미지는 16~20장 (지금 %d). 3초당 1장" % nbeat)
    raw_style = data.get("style") or {}
    if raw_style and not isinstance(raw_style, dict):
        raise ValueError("style 은 객체")
    style = Style(
        anchor=str((raw_style or {}).get("anchor") or "").strip(),
        face=str((raw_style or {}).get("face") or "").strip(),
        wardrobe=str((raw_style or {}).get("wardrobe") or "").strip(),
        mood=str((raw_style or {}).get("mood") or "").strip(),
    )
    tags = [str(t).strip() for t in (data.get("tags") or []) if str(t).strip()]
    script = Script(
        title=title,
        description=str(data.get("description") or "").strip(),
        tags=tags,
        hashtags=str(data.get("hashtags") or "").strip(),
        scenes=scenes,
        style=style,
    )
    from shorts.copy import validate_script

    validate_script(script)
    return script


def scene_image_path(job_dir: Path, index: int) -> Path:
    return job_dir / ("scene-%02d.png" % index)


def beat_image_path(job_dir: Path, index: int) -> Path:
    return job_dir / ("beat-%02d.png" % index)


def beat_media_path(job_dir: Path, index: int) -> Path | None:
    for suffix in (".png", ".jpg", ".jpeg", ".webp"):
        path = job_dir / ("beat-%02d%s" % (index, suffix))
        if path.is_file() and path.stat().st_size > 0:
            return path
    return None


def scene_media_path(job_dir: Path, index: int) -> Path | None:
    for suffix in (".png", ".jpg", ".jpeg", ".webp"):
        path = job_dir / ("scene-%02d%s" % (index, suffix))
        if path.is_file() and path.stat().st_size > 0:
            return path
    return None


def slugify(title: str, limit: int = 24) -> str:
    text = re.sub(r"[^\w가-힣]+", "-", title, flags=re.UNICODE).strip("-")
    return (text[:limit] or "short").strip("-")
