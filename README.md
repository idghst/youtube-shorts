# 유튜브 쇼츠 파이프라인

얼굴 없는 재테크 쇼츠. **대본·이미지는 Cursor 에이전트**, 나머지는 로컬 CLI.

외부 OpenAI/Gemini/FAL 호출 없음. TTS 없음. 영상은 이미지 + Ken Burns + 자막 + 무료 BGM.

## 준비

```bash
cd "/Users/idghst/.cursor/프로젝트/유튜브 쇼츠"
python3 -m pip install -r requirements.txt
```

- `ffmpeg` — 이 Mac에 있음 (`/opt/homebrew/bin/ffmpeg`). 없으면 `brew install ffmpeg`. 없으면 렌더하지 않음.
- YouTube 업로드 시에만 Google Cloud Desktop OAuth JSON을 `client_secrets.json`으로 루트에 두고 `python -m shorts auth`.
- `.env`는 `.env.example` 복사. 비밀값 커밋 금지.

## 하루치 한 편

Cursor 채팅에서 「쇼츠 만들어」→ 프로젝트 스킬 `.cursor/skills/shorts-pipeline/SKILL.md`.

또는 단계만:

```bash
python -m shorts pick --channel 돈이웃
# 에이전트가 out/<channel>/<job>/script.json 작성 + GenerateImage → scene-01.png …
python -m shorts run --dry-run --dir out/<channel>/<job>
```

채널: `돈이웃` (한국 재테크, 기본), `offscn` (다른 채널. 폴더만). `--channel` 생략 시 돈이웃.

`pick`은 RSS 미사용 헤드라인 중 **시니어 관심**(연금·노후·건보·상속·예적금·부동산 등)을 먼저 고른다. 그런 기사가 없으면 기존처럼 금융 키워드 → 오전 한경/매경, 오후 로이터/CNBC → 최신순.

`AUTO_PUBLISH=0` 또는 `--dry-run` → YouTube 생략. `out/<channel>/<job>/`에 mp4 + script JSON.

```bash
AUTO_PUBLISH=1 python -m shorts run --dir out/<channel>/<job>   # 공개 업로드
python -m shorts auth
```

길이는 `script.json`의 `scenes[].duration` 합 (50~60초). 문장 늘려 시간 채우지 말 것.

## 자막

장면마다 `captions` 배열. 한 덩어리로 오래 띄우지 말고 문장 단위로 끊는다. 한 줄이 길면 2줄. 흰 글자 + 어두운 박스/외곽선, 하단 세이프 영역. 숫자·핵심어만 색/굵기. 키네틱 금지. 쇼츠에서 3초 안에 읽히는 호흡.

## BGM

나레이션 없음. `assets/bgm/`의 Mixkit / Pixabay Music / CC0 / YouTube Audio Library급 트랙만. 렌더가 길이에 맞게 trim·loop + fade. 유튜브 영상/음원을 yt-dlp로 뜯지 말 것. 출처는 `assets/bgm/README`.

## 스케줄

launchd + API 키 헤드리스 LLM은 쓰지 않음. 하루 2회가 필요하면 Cursor Automation cron(08:00 / 21:00)이 이 스킬을 실행하게 만들 것. 그 전엔 에이전트가 위 CLI만 호출.
