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
6. **이미지**: 아래 **이미지 (Grok Imagine)** 절로 `image_prompt`를 쓴 뒤, 장면마다 Cursor **GenerateImage** (`aspect_ratio: 9:16`) → `scene-01.png` …. 걱정하는 시니어(사람) 없는 컷 금지. imagegen CLI / OPENAI_API_KEY 폴백 금지.
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
    {"text": "가계빚이 2000조를 넘겼어요. 이자가 더 문제예요", "duration": 11, "captions": ["가계빚 2000조요", "이자가 더 문제예요"], "image_prompt": "A vertical 9:16 photorealistic cinematic shot of a worried Korean senior in his late 60s sitting at an apartment dining table at midnight, staring at unsigned loan folders and paper bills with a tense frown. Moody teal-orange lamp light, raw realistic texture, clean empty floor in the bottom third for subtitles."},
    {"text": "영끌과 빚투가 밀어 올렸어요. 늘어난 빚의 열 중 여덟이 주담대예요", "duration": 12, "captions": ["영끌이랑 빚투가 밀었어요", "늘분의 열 중 여덟이 주담대"], "image_prompt": "A vertical 9:16 cinematic photo of a worried Korean senior woman standing on wet asphalt, watching a small suburban house being pulled by thick iron chains toward a dark unmarked stone building. Her hands clutch her coat, moonlight and cold fog, 35mm lens, empty dark ground at the bottom third."},
    {"text": "은행 한도를 넓히면 더 늘 수 있어요. 연체는 10년 만에 제일 높아요", "duration": 12, "captions": ["한도를 넓히면 더 늘어요", "연체는 10년 만에 최고예요"], "image_prompt": "A vertical 9:16 cinematic still of a worried Korean senior man watching a cracked hourglass leak gold coins onto a blank bank ledger in a dusty shaft of light. No readable numbers. Museum lighting, anxious mood, empty dark floor at the bottom."},
    {"text": "금리가 오르면 이자만 3조가 더 붙어요", "duration": 11, "captions": ["금리 오르면 이자만", "3조가 더 붙어요"], "image_prompt": "A vertical 9:16 photoreal concept of a worried Korean senior couple staring at a giant bronze lever in a marble hall tipping a household balance scale stacked with house keys and a tiny model home. Red-gold warning light from below, no digits or logos, clean lower third."},
    {"text": "빚이 월급보다 먼저 커지면 금리에 한 번에 흔들려요", "duration": 10, "captions": ["빚이 월급보다 먼저 컸어요", "금리에 한 번에 흔들려요"], "image_prompt": "A vertical 9:16 documentary still of a worried Korean senior woman looking at house keys and a closed unmarked folder on a wooden table beside a pale morning window. Quiet and serious, no phone UI, empty wall and floor in the bottom third."}
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

## 이미지 (Grok Imagine)

**필수:** 모든 장면 이미지에 걱정하는 시니어(사람)가 보여야 한다. 정물만·빈 방·사람 없음 금지.

Grok Imagine(FLUX)은 쉼표 키워드보다 **이어지는 2~3개 완전한 영어 문장**을 더 잘 따른다. `image_prompt`와 GenerateImage 설명을 그 문장으로 쓴다.

공식: **[구도 및 비율] + [인물/사물의 핵심 행동 및 감정] + [배경과 환경 디테일] + [카메라 렌즈·조명·화풍] + [자막 여백]**

| 단계 | 역할 | 작성법 |
| --- | --- | --- |
| 1. 구도/비율 | 세로 비율 및 피사체 위치 | `A vertical 9:16 mobile wallpaper framing, centered subject...` |
| 2. 주체/행동 | 걱정하는 시니어(사람) 필수 | `A worried Korean senior in his late 60s staring at unpaid bills with a tense frown...` |
| 3. 환경/소품 | 공간감과 세부 요소 | `in a messy dark office at midnight, scattered paperwork and glowing screen...` |
| 4. 화풍/조명 | 실사 렌즈 or 스타일 | `Shot on 35mm cinematic lens, moody volumetric lighting, raw realistic texture.` |
| 5. 세이프존 | 자막 공간 확보 | `Leave clean negative space at the bottom third of the frame for subtitles.` |

작성:

- 자연어 문장. ❌ `ancient egypt, pharaoh, 8k, realistic, --ar 9:16` / `Use case: photorealistic-natural` 필드 나열. ⭕ `A vertical 9:16 cinematic photo of an archaeologist uncovering a glowing artifact in a dark Egyptian tomb. The lighting comes from a beam of dust-filled sunlight.`
- 영문 텍스트가 필요할 때만 큰따옴표로 명시. 예: `A neon sign in the background displaying the word "WARNING".` 한글·숫자·퍼센트·로고·워터마크·실존 유명인 얼굴 금지. 기본은 글자 없이.
- **필수: 모든 장면에 걱정하는 시니어(사람)가 보여야 함.** 한국인 60대 전후, 불안·한숨·미간을 찌푸리는 표정/몸짓. 정물만·빈 방·사람 없음·손만·실루엣만 금지. 실존 유명인 얼굴은 금지, 가상의 시니어 얼굴은 됨.
- 현장감: `Shot on modern smartphone camera`, `Dashcam footage style`, `CCTV angle`, `Candid street photography`. 인공 3D보다 직찍.
- 돈이웃 기본은 극사실/UGC. 픽사·디즈니풍 금지.

템플릿 (장면 맞게 고쳐서 씀):

충격/지식 다큐:

```text
A vertical 9:16 photorealistic cinematic shot of a worried Korean senior in his late 60s sitting at an apartment dining table at midnight, staring at unsigned loan folders and paper bills. His shoulders are tense and his brow is furrowed. The scene is illuminated by teal-orange practical lamps and quiet city light through the window. Shot on a 35mm anamorphic lens, raw film texture, empty dark floor at the bottom.
```

뉴스/이슈 직찍:

```text
A vertical 9:16 authentic candid smartphone photo of a worried Korean senior woman in a crowded Seoul subway at rush hour. She grips a worn wallet and an unmarked transit card, brow furrowed, while other commuters stay unrecognizable in motion blur. Overhead lighting, realistic noise texture, clean lower area.
```

표지형 (영문 사인만):

```text
A vertical 9:16 dramatic still of a worried Korean senior man standing at a luxury penthouse window overlooking a city skyline at night. A soft neon sign in the glass reflection reads "SECRET". High contrast moody cinematic lighting, plenty of dark empty space at the bottom for captions.
```

## 대본 사실

- 헤드라인·요약만. 기사 복제 금지.
- 헤드라인에 없는 숫자·목표가 금지.
- 매수/매도/추천 금지.
- 이미지 프롬프트는 위 Grok Imagine 절. 영어 2~3문장. 하단 1/3 비움. 걱정하는 시니어(사람) 필수.

## 금지

- TTS (`say`, edge-tts, ElevenLabs, OpenAI TTS, Cursor TTS)
- 유튜브 영상/음원 yt-dlp
- `OPENAI_API_KEY` / `GEMINI_API_KEY` / `FAL_KEY`
- imagegen CLI (`scripts/image_gen.py`)
- 렌더 위조 (ffmpeg 없으면 중단)
