# 유튜브 쇼츠 파이프라인

장편 애니 화풍 정지 컷으로 만든 재테크 쇼츠. **대본·이미지는 Cursor 에이전트**, 나머지는 로컬 CLI.

외부 OpenAI/Gemini/FAL 호출 없음. TTS 없음. 영상은 정지 이미지 + 외곽선 자막 + 무료 BGM. **줌·검정 레터박스·동영상 클립 없음.** 한 편 안 얼굴·나이·의상은 `style.face`·`style.wardrobe`로 고정. 이미지는 3초당 1장.

## 준비

```bash
cd "/Users/idghst/.cursor/프로젝트/youtube-shorts"
.venv/bin/python -m pip install -r requirements.txt
```

- `ffmpeg` — 이 Mac에 있음 (`/opt/homebrew/bin/ffmpeg`). 없으면 `brew install ffmpeg`. 없으면 렌더하지 않음.
- YouTube 업로드 시에만 Google Cloud Desktop OAuth JSON을 `client_secrets.json`으로 루트에 두고 `.venv/bin/python -m shorts auth`.
- `.env`는 `.env.example` 복사. 비밀값 커밋 금지.

## 하루치 한 편

Cursor 채팅에서 「쇼츠 만들어」→ 프로젝트 스킬 `.cursor/skills/shorts-pipeline/SKILL.md`.

또는 단계만:

```bash
.venv/bin/python -m shorts pick --channel 돈이웃
# 에이전트가 out/<channel>/<job>/script.json 작성 + GenerateImage → beat-01.png … (3초당 1장)
.venv/bin/python -m shorts run --dry-run --dir out/<channel>/<job>
```

채널: `돈이웃` (한국 재테크, 기본), `offscn` (다른 채널. 폴더만). `--channel` 생략 시 돈이웃.

`pick`은 RSS 미사용 헤드라인 중 **통장·이체·한도·예금보호·부모 전세**를 시니어 국가통계보다 먼저 고른다. 은평·2030·MZ·국가 조 단위는 뒤로. 숫자·삭감·인상 훅이 있으면 가산.

같은 채널에 같은 헤드라인을 두 번 올리지 않는다. `pick`이 Supabase `youtube.uploads`를 보고 선점하고, 렌더/업로드 후 상태를 넣는다. Studio로 올릴 때는 `.venv/bin/python -m shorts meta --dir <잡>` 출력을 그대로 쓰고, 세부정보에서 `자세히`를 누른 뒤 아래로 스크롤해 해시태그 칸을 채운다. 올린 뒤 `.venv/bin/python -m shorts record --dir <잡> --status uploaded --video-id <id>`.

`AUTO_PUBLISH=0` 또는 `--dry-run` → YouTube 생략. `out/<channel>/<job>/`에 mp4 + script JSON.

```bash
AUTO_PUBLISH=1 .venv/bin/python -m shorts run --dir out/<channel>/<job>
.venv/bin/python -m shorts auth
```

길이는 `script.json`의 `scenes[].duration` 합 (45~51초, 3초 배수). 권장 48초·이미지 16장. 60초를 넘기면 Shorts 선반에서 밀린다. 제목은 억·만·원·% + 한도·세금 결과. 한 쇼츠 안 컷은 같은 `style.anchor`·`style.face`·`style.wardrobe`. 업로드 메타는 `.venv/bin/python -m shorts meta --dir <잡>`. 주제 해시태그 5~9개, 태그 10개 이상, `thumb.png` 필수. `#돈이웃` `#쇼츠` `#shorts`는 넣지 않는다.

흐름: Supabase 이전 주제 → 선정 → 화풍 고정 → 대본 → 제목 → 설명 → 해시태그 → 이미지 → 렌더 → 업로드 → Supabase 기록.

## 자막

대본 자막은 메시지·공포 우선. 산책·창밖 정서 금지. 장면마다 `captions` 2개 이상. 한 줄 = 사실 또는 내 돈 위험. 제목 숫자는 자막에 그대로. 뉴스 용어는 쉬운 말로. 한 줄 28자 이하. 흰 글자 + 어두운 박스/외곽선, 하단 세이프 영역. 숫자·핵심어만 색/굵기. 키네틱 금지. 해요체·짧은 구어·질문. 첫 자막은 훅. 마지막은 내 돈.

## BGM

나레이션 없음. `assets/bgm/`의 Mixkit / Pixabay Music / CC0 / YouTube Audio Library급 트랙만. 렌더가 길이에 맞게 trim·loop + fade. 유튜브 영상/음원을 yt-dlp로 뜯지 말 것. 출처는 `assets/bgm/README`.

## 스케줄

launchd + API 키 헤드리스 LLM은 쓰지 않음. 스케줄은 Cursor Automation cron이 `.cursor/skills/shorts-pipeline/SKILL.md`와 `.cursor/automations/돈이웃-시간별-쇼츠.md`를 실행한다. Studio 업로드 때 해시태그는 `자세히`를 누르고 스크롤해서 칸에 넣는다.
