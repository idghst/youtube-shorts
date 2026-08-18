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


@dataclass
class Beat:
    image_prompt: str


@dataclass
class Style:
    anchor: str
    face: str
    wardrobe: str
    mood: str

    def to_json(self) -> dict:
        return {
            "anchor": self.anchor,
            "face": self.face,
            "wardrobe": self.wardrobe,
            "mood": self.mood,
        }

    @classmethod
    def from_json(cls, data: dict | None) -> "Style | None":
        if not data or not isinstance(data, dict):
            return None
        anchor = str(data.get("anchor") or "").strip()
        face = str(data.get("face") or "").strip()
        wardrobe = str(data.get("wardrobe") or "").strip()
        mood = str(data.get("mood") or "").strip()
        if not (anchor or face or wardrobe or mood):
            return None
        return cls(anchor=anchor, face=face, wardrobe=wardrobe, mood=mood)


@dataclass
class Scene:
    text: str
    image_prompt: str
    duration: float
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

    def beat_count(self) -> int:
        return sum(len(s.beats or []) for s in self.scenes)

    def to_json(self) -> dict:
        scenes = []
        for s in self.scenes:
            item = {
                "text": s.text,
                "image_prompt": s.image_prompt,
                "duration": s.duration,
            }
            if s.captions:
                item["captions"] = list(s.captions)
            if s.beats:
                item["beats"] = [{"image_prompt": b.image_prompt} for b in s.beats]
            scenes.append(item)
        data = {
            "title": self.title,
            "description": self.description,
            "tags": list(self.tags),
            "scenes": scenes,
        }
        if self.hashtags:
            data["hashtags"] = self.hashtags
        if self.style:
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
        prompt = str(raw.get("image_prompt") or "").strip()
        try:
            duration = float(raw.get("duration"))
        except (TypeError, ValueError):
            raise ValueError("scenes[%d] 에 duration(초) 필요" % i)
        if duration <= 0:
            raise ValueError("scenes[%d] duration 은 0보다 커야 함" % i)
        raw_caps = raw.get("captions") or []
        if raw_caps and not isinstance(raw_caps, list):
            raise ValueError("scenes[%d] captions 는 배열" % i)
        captions = [str(c).strip() for c in raw_caps if str(c).strip()]
        raw_beats = raw.get("beats") or []
        if raw_beats and not isinstance(raw_beats, list):
            raise ValueError("scenes[%d] beats 는 배열" % i)
        beats = []
        for j, beat in enumerate(raw_beats, 1):
            if not isinstance(beat, dict):
                raise ValueError("scenes[%d] beats[%d] 는 객체" % (i, j))
            beat_prompt = str(beat.get("image_prompt") or "").strip()
            if not beat_prompt:
                raise ValueError("scenes[%d] beats[%d] 에 image_prompt 필요" % (i, j))
            beats.append(Beat(image_prompt=beat_prompt))
        if not prompt and beats:
            prompt = beats[0].image_prompt
        if not text or not prompt:
            raise ValueError("scenes[%d] 에 text/image_prompt 필요" % i)
        scenes.append(
            Scene(text=text, image_prompt=prompt, duration=duration, captions=captions, beats=beats)
        )
    title = str(data.get("title") or "").strip()
    if not title:
        raise ValueError("title 필요")
    if not scenes:
        raise ValueError("scenes 가 비어 있음")
    if not (4 <= len(scenes) <= 5):
        raise ValueError("scenes 는 4~5개")
    total = sum(s.duration for s in scenes)
    if not (50 <= total <= 60):
        raise ValueError("장면 duration 합은 50~60초 (지금 %.1f)" % total)
    tags = [str(t).strip() for t in (data.get("tags") or []) if str(t).strip()]
    script = Script(
        title=title,
        description=str(data.get("description") or "").strip(),
        tags=tags,
        hashtags=str(data.get("hashtags") or "").strip(),
        scenes=scenes,
        style=Style.from_json(data.get("style")),
    )
    from shorts.copy import validate_script

    validate_script(script)
    return script


def scene_image_path(job_dir: Path, index: int) -> Path:
    return job_dir / ("scene-%02d.png" % index)


def beat_image_path(job_dir: Path, index: int) -> Path:
    return job_dir / ("beat-%02d.png" % index)


def slugify(title: str, limit: int = 24) -> str:
    text = re.sub(r"[^\w가-힣]+", "-", title, flags=re.UNICODE).strip("-")
    return (text[:limit] or "short").strip("-")
