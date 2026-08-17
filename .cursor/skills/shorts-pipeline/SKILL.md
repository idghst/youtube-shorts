---
name: shorts-pipeline
description: Makes one Korean finance YouTube Short from RSS via local CLI plus Cursor GenerateImage. Use when the user asks to make a Short, 쇼츠, run the shorts pipeline, write a script.json, generate scene images, render, or upload.
---

# 쇼츠 파이프라인

에이전트가 하루치(헤드라인 1개 → 쇼츠 1개)를 만든다. 외부 LLM/이미지 HTTP API 금지. TTS 없음. 영상은 이미지 + Ken Burns + 화면 자막 + 무료 BGM.

산출은 `out/<channel>/<job>/`. 채널 두 개: **돈이웃** (한국 재테크, 현재 RSS 파이프라인), **offscn** (다른 채널. 폴더만. 콘텐츠 파이프라인은 아직 없음). 기본 채널은 돈이웃.

없음: 헤드리스 launchd LLM. 스케줄은 Cursor Automation cron이 이 스킬을 돌리는 방식. 자동화 프롬프트는 `.cursor/automations/돈이웃-시간별-쇼츠.md`.

중복은 Supabase `youtube.uploads`가 채널별로 막는다. pick이 해시·이전 제목을 보고 선점하고, 렌더/업로드 후에 상태를 넣는다. 로컬 `data/shorts.db`만 보지 마라.

## 실행 순서

저장소 루트에서. 이 순서를 건너뛰거나 한 파일에 대충 몰아 쓰지 말 것.

1. **이전 주제** + **주제 선정**: `python -m shorts pick --channel 돈이웃` → stdout이 잡 폴더. pick이 `youtube.uploads` 해시와 이전 제목을 빼고 고른 뒤 `picked`로 선점한다. 시니어 관심(연금·노후·건보·상속·예적금·부동산)을 금융 일반·최신 기사보다 우선. “쓸 헤드라인 없음”이면 중단.
2. **대본**: `headline.json`과 `used-topics.json`을 보고 `script.json`의 `scenes`만 먼저 쓴다. OpenAI/Gemini HTTP 금지. 이전 제목과 같은 각도·같은 훅 금지.
3. **제목**: 대본을 본 뒤에 `title`을 쓴다. 대본 첫 줄을 옮기지 말 것.
4. **설명**: 제목 다음에 `description` 본문만. 해시태그·면책 넣지 말 것.
5. **해시태그**: `hashtags`와 `tags`. 그다음 `script.json`을 저장.
6. **이미지**: 장면마다 Cursor **GenerateImage** (`aspect_ratio: 9:16`) → `scene-01.png` …. imagegen CLI / OPENAI_API_KEY 폴백 금지.
7. **영상**: `python -m shorts run --dry-run --dir out/<channel>/<job>` → `video.mp4`. duration 합 50~60초. 성공 시 `rendered`.
8. **업로드**: 사용자가 `올려줘`/`업로드` 할 때, 또는 시간별 자동화일 때. **REQUIRED:** `.cursor/skills/shorts-upload/SKILL.md`.
9. **기록**: Studio로 올렸으면 `python -m shorts record --dir out/<channel>/<job> --status uploaded --video-id <id>`.

실패 시 로그만 남기고 중단. picked/rendered/uploaded 해시는 같은 채널에서 다시 pick하지 않는다.

## script.json

대본 → 제목 → 설명 → 해시태그 순으로 채운다. 한 번에 복붙하지 말 것.

```json
{
  "title": "가계빚 2000조, 이자만 3조 더?",
  "description": "영끌이랑 빚투로 가계빚이 처음 2000조를 넘겼어요. 늘어난 빚의 열 중 여덟이 주택담보대출이고, 금리가 오르면 이자만 3조가 더 붙는다는 얘기예요.",
  "tags": ["가계빚", "주담대", "영끌", "금리인상", "재테크"],
  "hashtags": "#가계빚 #주담대 #영끌 #금리인상 #돈이웃 #쇼츠 #shorts",
  "scenes": [
    {"text": "가계빚이 2000조를 넘겼어요. 이자가 더 문제예요", "duration": 11, "captions": ["가계빚 2000조요", "이자가 더 문제예요"], "image_prompt": "English, 9:16, no text/logos"},
    {"text": "영끌과 빚투가 밀어 올렸어요. 늘어난 빚의 열 중 여덟이 주담대예요", "duration": 12, "captions": ["영끌이랑 빚투가 밀었어요", "늘분의 열 중 여덟이 주담대"], "image_prompt": "..."},
    {"text": "은행 한도를 넓히면 더 늘 수 있어요. 연체는 10년 만에 제일 높아요", "duration": 12, "captions": ["한도를 넓히면 더 늘어요", "연체는 10년 만에 최고예요"], "image_prompt": "..."},
    {"text": "금리가 오르면 이자만 3조가 더 붙어요", "duration": 11, "captions": ["금리 오르면 이자만", "3조가 더 붙어요"], "image_prompt": "..."},
    {"text": "빚이 월급보다 먼저 커지면 금리에 한 번에 흔들려요", "duration": 10, "captions": ["빚이 월급보다 먼저 컸어요", "금리에 한 번에 흔들려요"], "image_prompt": "..."}
  ]
}
```

scenes 4~5개. 훅 + 비트 + 정리. `duration` 합 50~60. 대본은 화면 자막만. 문장 늘려 시간 채우지 말 것. `load_script`가 카피를 검사한다.

## 제목 (클릭·검색)

- 해시태그 넣지 말 것. 12~42자.
- 헤드라인이나 첫 자막을 습니다로 옮기지 말 것.
- 검색어 + 궁금증. 숫자·결과·질문 중 하나.
- 입니다/습니다/나왔습니다 금지.
- 예: `가계빚 2000조, 이자만 3조 더?` / 비예: `가계빚이 사상 처음으로 2000조를 넘었습니다`

## 설명 (검색·체류)

- 본문만. 해시태그·면책은 필드/코드가 붙임.
- 첫 줄은 제목 복붙 금지. 2~3문장: 무슨 일 + 왜 내 돈과 관련.
- 해요체. 습니다 나열 금지.

## 해시태그 (노출)

- `hashtags` 5~10개. 구체 → 중간 → `#돈이웃 #쇼츠 #shorts`.
- 앞에 `#재테크 #경제`만 두지 말 것. 주제 태그 2개 이상.
- `tags`는 해시태그에서 `#` 뺀 검색어.

## 대본 (유지·조회)

- 장면1 훅: 질문이거나 덜 끝난 말. 결론을 첫 자막에 다 쏟지 말 것. 제목을 그대로 읽지 말 것.
- 장면마다 새 정보 하나. 같은 사실 3번 반복 금지.
- 마지막: 내 대출/이자/월급에 미치는 한 줄. 「다시 살펴볼 시점」 금지.
- 면책 장면 금지. 면책은 설명에만.
- `used-topics.json`과 같은 훅·같은 각도 금지.

## 문체 (AI 티 빼기) — 최우선

사람 말처럼. 뉴스 앵커/리포트 말투면 다시 쓴다.

- 해요체 + 짧은 구어 + 질문. 문장 길이 들쭉날쭉.
- 습니다/입니다는 자막 전체에서 많아 봐야 1개. 없으면 더 좋음.
- 음슴체·~다 체·명사 나열만으로 된 장면 금지.
- 제목 ≠ 첫 자막 ≠ 설명 첫 문장.

금지어(자막·제목·설명 전부):

`알아보겠습니다` `살펴보겠습니다` `살펴볼 시점` `다시 한번 살펴` `다시 한번 정리` `핵심을 정리` `많은 분들이` `오늘 알아볼` `함께 알아` `함께 살펴` `라는 표현입니다` `헤드라인에` `매수나 매도 신호` `목표가는 나오지` `정보 제공이 목적` `결론적으로` `첫째` `둘째` `셋째` `마지막으로`

## 자막

- `captions`로 장면/문장 단위로 끊는다. 장면당 2개 이상. 한 줄 28자 이하.
- 처음 보는 사람이 3초 안에 뜻을 알게. 뉴스 용어는 쉬운 말로.
- 한 컷에 생각 하나. 메타 자막 금지.
- 가독성: 큰 글씨, 흰 글자 + 어두운 박스/외곽선, 좌우 여백, 길면 2줄, 하단 세이프 영역.
- 숫자·핵심어만 색/굵기. 키네틱 금지.
- 예: 「총량 목표를 완화하면」→「은행이 빌려줄 수 있는 한도를 넓히면」. 「수주물량 70%」→「새로 들어온 일감 열 건 중 일곱」.

## BGM

나레이션/`say`/외부 TTS 없음. `assets/bgm/`의 Mixkit · Pixabay Music · CC0 · YouTube Audio Library급만. 유튜브 음원 yt-dlp 금지. 출처는 `assets/bgm/README` 한 줄.

## 대본 사실

- 헤드라인·요약만. 기사 복제 금지.
- 헤드라인에 없는 숫자·목표가 금지.
- 매수/매도/추천 금지.
- 이미지 프롬프트는 영어. 글자·로고·실존 인물 얼굴 넣지 말 것. 세로 구도.

## 금지

- TTS (`say`, edge-tts, ElevenLabs, OpenAI TTS, Cursor TTS)
- 유튜브 영상/음원 yt-dlp
- `OPENAI_API_KEY` / `GEMINI_API_KEY` / `FAL_KEY`
- imagegen CLI (`scripts/image_gen.py`)
- 렌더 위조 (ffmpeg 없으면 중단)
