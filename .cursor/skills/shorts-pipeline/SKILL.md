---
name: shorts-pipeline
description: Makes one Korean finance YouTube Short from RSS via local CLI plus Cursor GenerateImage. Use when the user asks to make a Short, 쇼츠, run the shorts pipeline, write a script.json, generate scene images, render, or upload.
---

# 쇼츠 파이프라인

에이전트가 하루치(헤드라인 1개 → 쇼츠 1개)를 만든다. 외부 LLM/이미지 HTTP API 금지. TTS 없음. 영상은 이미지 + Ken Burns + 화면 자막 + 무료 BGM.

산출은 `out/<channel>/<job>/`. 채널 두 개: **돈이웃** (한국 재테크, 현재 RSS 파이프라인), **offscn** (다른 채널. 폴더만. 콘텐츠 파이프라인은 아직 없음). 기본 채널은 돈이웃.

없음: 헤드리스 launchd LLM. 스케줄은 Cursor Automation cron이 이 스킬을 돌리는 방식. 자동화 프롬프트는 `.cursor/automations/돈이웃-시간별-쇼츠.md`.

중복은 Supabase `youtube.uploads`가 채널별로 막는다. pick이 테이블을 보고 선점하고, 렌더/업로드 후에 상태를 넣는다. 로컬 `data/shorts.db`만 보지 마라.

## 실행 순서

저장소 루트에서.

1. `python -m shorts pick --channel 돈이웃` → `out/<channel>/<job>/headline.json` 경로가 stdout. (`--channel offscn` 가능. 생략 시 돈이웃). pick은 `youtube.uploads`에서 해당 채널의 picked/rendered/uploaded 해시를 빼고, 고른 뒤 `picked`로 선점한다. 시니어 관심(연금·노후·건보·상속·예적금·부동산) 헤드라인을 금융 일반·최신 기사보다 우선한다. “쓸 헤드라인 없음”이면 중단.
2. `headline.json`만 보고 **원본** `script.json`을 같은 폴더에 직접 작성. OpenAI/Gemini/기타 LLM HTTP 호출 금지.
3. 장면마다 Cursor **GenerateImage** (`aspect_ratio: 9:16`). 결과를 `out/<channel>/<job>/scene-01.png` … 로 복사. imagegen CLI / OPENAI_API_KEY 폴백 금지.
4. `python -m shorts run --dry-run --dir out/<channel>/<job>`
   - ffmpeg 1080x1920 Ken Burns + 자막 + `assets/bgm` 루프/페이드
   - 길이는 `scenes[].duration` 합 (50~60초)
   - YouTube 생략. `video.mp4` + `script.json` 유지
   - 성공 시 `youtube.uploads.status=rendered`
5. 공개 업로드는 사용자가 `올려줘`/`업로드` 할 때, 또는 시간별 자동화가 게시할 때. **REQUIRED:** `.cursor/skills/shorts-upload/SKILL.md`. 크롬 computerUse가 기본(하단 독 아이콘 → 열린 창에서 `navigate`). CLI는 `token.json` 있을 때만 `AUTO_PUBLISH=1 python -m shorts upload --dir out/<channel>/<job>`.
6. Studio로 올렸으면 `python -m shorts record --dir out/<channel>/<job> --status uploaded --video-id <id>`.

실패 시 로그만 남기고 중단. picked/rendered/uploaded 해시는 같은 채널에서 다시 pick하지 않는다.

## script.json

```json
{
  "title": "훅 제목 #Shorts",
  "description": "두세 문장. 코드가 면책과 #Shorts를 덧붙임",
  "tags": ["재테크", "경제", "주식"],
  "hashtags": "#재테크 #경제 #Shorts",
  "scenes": [
    {"text": "훅", "duration": 11, "captions": ["훅 한 줄", "숫자 한 방"], "image_prompt": "English, 9:16, no text/logos"},
    {"text": "비트1", "duration": 12, "captions": ["문장1", "문장2"], "image_prompt": "..."},
    {"text": "비트2", "duration": 12, "captions": ["문장1", "문장2"], "image_prompt": "..."},
    {"text": "비트3", "duration": 11, "captions": ["문장1", "문장2"], "image_prompt": "..."},
    {"text": "한 줄 정리", "duration": 10, "captions": ["정리 앞", "정리 뒤"], "image_prompt": "..."}
  ]
}
```

scenes 4~5개. 훅 + 3비트 + 정리. `duration` 합 50~60. 대본은 화면 자막만. 문장 늘려 시간 채우지 말 것.

## 자막

- 대본 자막은 이해하기 쉽게 작성해야 함.
- `captions`로 장면/문장 단위로 끊는다. 대본 전체를 한 덩어리로 오래 띄우지 말 것.
- 처음 듣는 사람이 3초 안에 뜻을 알게. 뉴스 용어·약어는 쉬운 말로 풀거나 바로 이어서 설명.
- 한 컷에 생각 하나. 메타 자막 금지(「헤드라인에 숫자는 없습니다」, 「~라는 표현입니다」).
- 문체: ~입니다/~습니다. 명사체·음슴체·~다 체 금지.
- 가독성: 큰 글씨, 흰 글자 + 어두운 박스/외곽선, 좌우 여백, 길면 2줄, 하단 세이프 영역.
- 숫자·핵심어만 색/굵기. 키네틱·산만함 금지. 쇼츠에서 3초 안에 읽히는 호흡.
- 예: 「총량 목표를 완화하면」→「은행이 빌려줄 수 있는 한도를 넓히면」. 「수주물량 70%」→「새로 들어온 일감 열 건 중 일곱」.

## BGM

나레이션/`say`/외부 TTS 없음. `assets/bgm/`의 Mixkit · Pixabay Music · CC0 · YouTube Audio Library급만. 유튜브 음원 yt-dlp 금지. 출처는 `assets/bgm/README` 한 줄.

## 대본 규칙

- 대본 자막은 이해하기 쉽게 작성해야 함. `text`와 `captions` 모두.
- 헤드라인·요약만. 기사 복제 금지.
- 헤드라인에 없는 숫자·목표가 금지.
- 매수/매도/추천 금지. 면책은 설명에만. 자막으로 반복하지 말 것.
- 이미지 프롬프트는 영어. 글자·로고·실존 인물 얼굴 넣지 말 것. 세로 구도.

## 금지

- TTS (`say`, edge-tts, ElevenLabs, OpenAI TTS, Cursor TTS)
- 유튜브 영상/음원 yt-dlp
- `OPENAI_API_KEY` / `GEMINI_API_KEY` / `FAL_KEY`
- imagegen CLI (`scripts/image_gen.py`)
- 렌더 위조 (ffmpeg 없으면 중단)
