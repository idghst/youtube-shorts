# Agent Instructions

[git]
- 사용자 요청 작업이 완료되면 `idghst-git-commit-push-korean`(`/Users/idghst/.codex/skills/idghst-git-commit-push-korean/SKILL.md`)을 바로 실행한다.
- 이번 세션에서 만든 변경만 한글 제목으로 커밋하고 현재 브랜치를 `git push`한다.
- `.env`, credentials, token, 비밀값, 이번 작업과 무관한 dirty 파일은 제외하고 남은 파일은 보고한다.
- force push, 자동 pull/rebase/merge, `--no-verify`는 명시 요청 없이 하지 않는다.
- 커밋할 변경이 없으면 커밋하지 않는다.
- 파이프라인·카피·선정 개선이 생기면 그 변경을 먼저 `main`에 커밋·푸시한다. `.cursor/automations/` 지침은 `main`에 올라간 뒤에만 맞춘다.

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

1. `.venv/bin/python -m shorts pick --channel 돈이웃` → 이전 주제 조회 후 선정, `headline.json` + `used-topics.json`. 통장·한도·이체·월세 만 원이 시니어 조 단위보다 앞. 같은 한도·월세+숫자는 재탕으로 건너뛴다. 전셋값 시세·코스피 수익률·적금 연%·육아휴직은 뒤로.
2. 에이전트가 `style.anchor`·`style.face`·`style.wardrobe`를 고정한 뒤 대본 → 제목 → 설명 → 해시태그 순으로 `script.json`을 쓰고 GenerateImage로 `beat-01.png` … 와 `thumb.png`(16:9) 작성. 3초당 1장. **45~51초/15~17장, 권장 48초/16장.** 제목은 전세·월세·부모·통장·한도 + **억/만 원**. 팔지말지·팔면·2030·지역·만 명·코스피·전셋값·적금 연%·육아휴직 제목 금지. 첫 자막에 그 숫자와 내 돈. 설명 앞 200자에 키워드. 해시태그·태그는 주제만(`#돈이웃` `#쇼츠` `#shorts` 금지, tags 10개+). 동영상 클립은 만들지 않는다. 직전 컷을 레퍼런스로 얼굴·옷·분위기를 고정. 한 쇼츠 안은 같은 얼굴·나이·의상·화풍. **자막은 숫자·공포·내 돈. 스토리는 그림만.** 손발 중복 금지. 장편 애니 톤. 실사 사람·망가체·줌 확대·검정 레터박스 금지. OpenAI/Gemini/FAL, imagegen CLI 금지. 해요체. 마지막은 내 돈. 구독 CTA 금지. thumb.png는 한 사람·단색 배경. 영상 프레임 금지.
3. `.venv/bin/python -m shorts run --dry-run --dir out/<channel>/<job>` → `video.mp4`. scenes 4~5개, duration은 3초 배수, 합 45~51초(권장 48초/16장). 60초 초과 금지. 제목은 전세·월세·부모·통장·한도 + 억/만 원. 첫 자막에 그 숫자. thumb.png 필수.
4. 업로드 후 `record`로 Supabase에 남겨 다음 pick이 중복을 피한다.

### 업로드

- 공개 업로드는 사용자 요청 또는 시간별 자동화일 때만. `client_secrets.json` 없으면 CLI 업로드 불가.
- Studio 메타: `.venv/bin/python -m shorts meta --dir <잡폴더>`. 제목·설명 후 **`자세히`를 누르고 아래로 스크롤**해서 해시태그 칸을 채운다. 설명의 `#`만으로는 안 붙는다. 상세는 `.cursor/skills/shorts-upload/SKILL.md`.

### 무시 경로

- `out/`, `data/*.db`, `.venv/`, `.env`, `token.json`, `client_secrets.json`은 커밋하지 않는다.
