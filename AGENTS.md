# Agent Instructions

[git]
- 사용자 요청 작업이 완료되면 `idghst-git-commit-push-korean`(`/Users/idghst/.codex/skills/idghst-git-commit-push-korean/SKILL.md`)을 바로 실행한다.
- 이번 세션에서 만든 변경만 한글 제목으로 커밋하고 현재 브랜치를 `git push`한다.
- `.env`, credentials, token, 비밀값, 이번 작업과 무관한 dirty 파일은 제외하고 남은 파일은 보고한다.
- force push, 자동 pull/rebase/merge, `--no-verify`는 명시 요청 없이 하지 않는다.
- 커밋할 변경이 없으면 커밋하지 않는다.

## Cursor Cloud

이 저장소는 로컬 YouTube Shorts 파이프라인(`shorts` + `ffmpeg`)이다. macOS용으로 쓰였고 Linux Cloud VM에서도 돈다. 제품/워크플로는 `README.md`, `.cursor/skills/shorts-pipeline/SKILL.md`.

### 실행

- 프로젝트 venv: `.venv/bin/python -m shorts <cmd>`. 시스템 Python에 설치하지 않는다.
- 렌더는 `ffmpeg`/`ffprobe` 필요. VM은 `/usr/bin/ffmpeg`.
- 점검: `.venv/bin/python -m py_compile shorts/*.py`, `python -m unittest`, 파이프라인 한 번.

### 한글 폰트

- macOS: `/System/Library/Fonts/AppleSDGothicNeo.ttc`, `.../Supplemental/AppleGothic.ttf`
- Linux: `shorts/render.py`의 `LINUX_FONTS` (Noto CJK/KR, Nanum, WenQuanYi)
- 둘 다 없으면 `한글 폰트 없음`으로 중단.

### 파이프라인

1. `.venv/bin/python -m shorts pick --channel 돈이웃` → 이전 주제 조회 후 선정, `headline.json` + `used-topics.json`
2. 에이전트가 대본 → 제목 → 설명 → 해시태그 순으로 `script.json`을 쓰고 `GenerateImage`로 `scene-01.png` … 작성. OpenAI/Gemini/FAL, imagegen CLI 금지. 해요체. 습니다 연속·메타 자막 금지.
3. `.venv/bin/python -m shorts run --dry-run --dir out/<channel>/<job>` → `video.mp4`. scenes 4~5개, duration 합 50~60초.
4. 업로드 후 `record`로 Supabase에 남겨 다음 pick이 중복을 피한다.

### 업로드

- 공개 업로드는 사용자 요청 또는 시간별 자동화일 때만. `client_secrets.json` 없으면 CLI 업로드 불가.

### 무시 경로

- `out/`, `data/*.db`, `.venv/`, `.env`, `token.json`, `client_secrets.json`은 커밋하지 않는다.
