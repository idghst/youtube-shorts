---
name: shorts-pipeline
description: Makes one Korean finance YouTube Short from RSS via local CLI plus Cursor GenerateImage. Use when the user asks to make a Short, 쇼츠, run the shorts pipeline, write a script.json, generate scene images, render, or upload.
---

# 쇼츠 파이프라인

에이전트가 하루치(헤드라인 1개 → 쇼츠 1개)를 만든다. 외부 LLM/이미지 HTTP API 금지. TTS 없음.

영상은 **정지 이미지** + 화면 자막 + 무료 BGM. 렌더가 이미지를 확대(줌)하지 않는다. 동영상 클립은 만들지 않는다.

산출은 `out/<channel>/<job>/`. 채널 두 개: **돈이웃** (한국 재테크), **offscn** (폴더만). 기본은 돈이웃.

없음: 헤드리스 launchd LLM. 스케줄은 Cursor Automation cron. 자동화 프롬프트는 `.cursor/automations/돈이웃-시간별-쇼츠.md`.

중복은 Supabase `youtube.uploads`가 채널별로 막는다. 로컬 `data/shorts.db`만 보지 마라.

목표 기획은 천만 조회수급(훅·숫자·내 돈·무음 가독). 조회수 보장은 코드가 하지 않는다.

유튜브 사실적 합성 라벨을 피하려면 **실사 사람 얼굴을 만들지 않는다.** 감지 회피 수작(노이즈·적대적 왜곡)은 하지 않는다. 장편 애니 화풍은 실사가 아니다.

## 실행 순서

저장소 루트에서. 이 순서를 건너뛰거나 한 파일에 대충 몰아 쓰지 말 것.

1. **이전 주제** + **주제 선정**: `.venv/bin/python -m shorts pick --channel 돈이웃` → stdout이 잡 폴더. 시니어 관심(연금·노후·건보·상속·예적금·부동산) 우선. 숫자·삭감·인상 같은 훅이 있으면 더 앞. “쓸 헤드라인 없음”이면 중단.
2. **이 쇼츠의 화풍 하나**: `style.anchor`·`style.face`·`style.wardrobe`를 먼저 고정한다. 쇼츠마다 달라도 된다. **한 쇼츠 안 컷은 같은 얼굴·나이·옷·마을·빛이어야 한다.**
3. **대본**: `headline.json`과 `used-topics.json`을 보고 `script.json`의 `scenes`만 먼저 쓴다. 장면은 스토리가 이어지게. OpenAI/Gemini HTTP 금지. 이전 제목과 같은 각도·같은 훅 금지.
4. **제목**: 대본을 본 뒤에 `title`. 대본 첫 줄을 옮기지 말 것. 숫자 또는 물음표 필수.
5. **설명**: 제목 다음에 `description` 본문만.
6. **해시태그**: `hashtags`와 `tags`. 그다음 `script.json`을 저장.
7. **이미지**: 아래 **화면** 절로 비트마다 프롬프트를 쓴 뒤, Cursor **GenerateImage** (`aspect_ratio: 9:16`) → `beat-01.png` …. 3초당 1장. 60초면 20장. 직전 컷(+ beat-01)을 레퍼런스로 얼굴·옷을 고정. 실사 사람·망가체 금지. 동영상 클립·imagegen CLI / OPENAI_API_KEY 폴백 금지.
8. **영상**: `.venv/bin/python -m shorts run --dry-run --dir out/<channel>/<job>` → `video.mp4`. duration은 3초 배수, 합 48~60초(권장 60초/20장). 성공 시 `rendered`.
9. **업로드**: 사용자가 `올려줘`/`업로드` 할 때, 또는 시간별 자동화일 때. **REQUIRED:** `.cursor/skills/shorts-upload/SKILL.md`. 먼저 `.venv/bin/python -m shorts meta --dir <잡폴더>`. Studio에서 제목·설명 다음에 **`자세히`를 누르고 아래로 스크롤**해서 해시태그 칸에 `meta.hashtags`를 넣는다. 설명의 `#`만으로 대체하지 마라. 태그 칸에는 `meta.tags`. 해시태그 칸이 비면 `다음` 금지.
10. **기록**: Studio로 올렸으면 `.venv/bin/python -m shorts record --dir out/<channel>/<job> --status uploaded --video-id <id>`.

실패 시 로그만 남기고 중단.

## script.json

대본 → 제목 → 설명 → 해시태그 순. 한 번에 복붙하지 말 것.

```json
{
  "title": "가계빚 2000조, 이자만 3조 더?",
  "description": "영끌이랑 빚투로 가계빚이 처음 2000조를 넘겼어요. 늘어난 빚의 열 중 여덟이 주택담보대출이고, 금리가 오르면 이자만 3조가 더 붙는다는 얘기예요.",
  "tags": ["가계빚", "주담대", "영끌", "금리인상", "재테크"],
  "hashtags": "#가계빚 #주담대 #영끌 #금리인상 #돈이웃 #쇼츠 #shorts",
  "style": {
    "anchor": "the same silver-haired Korean woman in a cream cardigan, painterly animated film, luminous dusk sky",
    "face": "same late-60s Korean woman, silver bob to the jaw, soft eye wrinkles, round cheeks, do not change age",
    "wardrobe": "same cream cardigan over ivory blouse every beat",
    "mood": "quiet hillside town, wet streets, glowing windows"
  },
  "scenes": [
    {
      "text": "가계빚이 2000조를 넘겼어요. 이자가 더 문제예요",
      "duration": 12,
      "captions": ["이자가 더 붙는다고요?", "가계빚이 2000조예요"],
      "beats": [
        {"image_prompt": "the same silver-haired Korean woman in a cream cardigan, painterly animated film, luminous dusk sky. same late-60s Korean woman, silver bob to the jaw, soft eye wrinkles, round cheeks, do not change age. same cream cardigan over ivory blouse every beat. exactly two hands and two feet, no extra limbs. She reads an unmarked envelope by the apartment window. Soft theatrical animation. Vertical 9:16."},
        {"image_prompt": "the same silver-haired Korean woman in a cream cardigan, painterly animated film, luminous dusk sky. same late-60s Korean woman, silver bob to the jaw, soft eye wrinkles, round cheeks, do not change age. same cream cardigan over ivory blouse every beat. exactly two hands and two feet, no extra limbs. She turns the envelope over with both hands. Soft theatrical animation. Vertical 9:16."},
        {"image_prompt": "the same silver-haired Korean woman in a cream cardigan, painterly animated film, luminous dusk sky. same late-60s Korean woman, silver bob to the jaw, soft eye wrinkles, round cheeks, do not change age. same cream cardigan over ivory blouse every beat. exactly two hands and two feet, no extra limbs. She looks out the dusk window, envelope at her chest. Soft theatrical animation. Vertical 9:16."},
        {"image_prompt": "the same silver-haired Korean woman in a cream cardigan, painterly animated film, luminous dusk sky. same late-60s Korean woman, silver bob to the jaw, soft eye wrinkles, round cheeks, do not change age. same cream cardigan over ivory blouse every beat. exactly two hands and two feet, no extra limbs. She steps back from the window, still holding the letter. Soft theatrical animation. Vertical 9:16."}
      ]
    }
  ]
}
```

scenes 4~5개. 훅 + 비트 + 정리. 장면 `duration`은 3초 배수, `beats` 개수 = duration/3. 합 48~60초. 권장 60초·이미지 20장(5장면×12초×4비트). 위 JSON은 장면 1만 예시. 나머지 장면도 beats 4개, 같은 하루로 행동이 이어지게. 대본은 화면 자막만. `load_script`가 카피·화풍을 검사한다.

## 제목 (클릭·검색)

- 해시태그 넣지 말 것. 12~42자.
- **숫자 또는 물음표 필수.**
- 헤드라인이나 첫 자막을 습니다로 옮기지 말 것.
- 입니다/습니다/나왔습니다 금지.
- 예: `가계빚 2000조, 이자만 3조 더?`

## 설명 (검색·체류)

- 본문만. 해시태그·면책은 필드/코드가 붙임.
- 첫 줄은 제목 복붙 금지. 2~3문장: 무슨 일 + 왜 내 돈과 관련.
- 해요체. 습니다 나열 금지.

## 해시태그 (노출)

- `hashtags` 5~10개. 구체 → 중간 → `#돈이웃 #쇼츠 #shorts`.
- 주제 태그 2개 이상.
- `tags`는 해시태그에서 `#` 뺀 검색어.

## 대본 (유지·조회)

- 장면1 훅: 질문이거나 덜 끝난 말. 결론을 첫 자막에 다 쏟지 말 것. 제목을 그대로 읽지 말 것.
- 장면마다 새 정보 하나. 같은 사실 3번 반복 금지.
- 마지막: 내 대출/이자/월급/연금에 미치는 한 줄.
- 면책 장면 금지. 면책은 설명에만.
- `used-topics.json`과 같은 훅·같은 각도 금지.

## 문체 (AI 티 빼기)

해요체 + 짧은 구어 + 질문. 습니다/입니다는 자막 전체에서 많아 봐야 1개.
제목 ≠ 첫 자막 ≠ 설명 첫 문장.

금지어: `알아보겠습니다` `살펴보겠습니다` `살펴볼 시점` `다시 한번 살펴` `다시 한번 정리` `핵심을 정리` `많은 분들이` `오늘 알아볼` `함께 알아` `함께 살펴` `라는 표현입니다` `헤드라인에` `매수나 매도 신호` `목표가는 나오지` `정보 제공이 목적` `결론적으로` `첫째` `둘째` `셋째` `마지막으로`

## 자막

- 장면당 `captions` 2개 이상. 한 줄 28자 이하.
- 무음으로 3초 안에 뜻을 알게. 뉴스 용어는 쉬운 말로.
- 숫자·핵심어만 색/굵기. 키네틱 금지.

## 화면 (3초 정지 컷)

동영상 클립은 만들지 않는다. **음악 3초마다 이미지가 바뀐다.** Cursor **GenerateImage** `aspect_ratio: 9:16` → `beat-01.png` … `beat-20.png`. 60초면 20장.

실사 사람 금지. 망가/만화잡지/치비/효과선 금지. 프롬프트에 manga, photoreal, zoom 단어를 넣지 말 것. 디즈니·지브리·신카이 장편 **느낌**. 특정 저작권 캐릭터 금지.

**한 쇼츠 = 한 `style.anchor` + 한 `style.face` + 한 `style.wardrobe`.** 모든 beat `image_prompt`에 세 문장과 `exactly two hands and two feet, no extra limbs`를 그대로 넣는다.

이어짐:
- 20장은 같은 하루의 연속 컷. 비트마다 행동이 한 걸음만 바뀐다. 갑자기 다른 사람·다른 옷·다른 마을이면 다시 생성.
- `style.face`에 나이·머리·이목구비를 잠근다. 예: `same late-60s Korean woman, silver bob to the jaw, soft eye wrinkles, round cheeks, do not change age`
- `style.wardrobe`에 겉옷·색을 잠근다. 컷마다 옷이 바뀌면 다시 생성.
- 손·발·팔이 같은 방향에 두 개·세 개면 버린다. 프롬프트에 해부 고정 문장을 빼지 마라.
- 먼저 `beat-01.png`. 다음부터는 `reference_image_paths`에 **직전 비트**와 `beat-01.png`를 넣고 같은 얼굴을 유지한다.
- 컷마다 젊어지거나 늙으면 다시 생성. 20s와 60s를 한 편에 섞지 마라.

쇼츠끼리는 화풍을 바꿔도 된다. 다음 편에 같은 구도·같은 훅 금지.

프롬프트: `style.anchor`. `style.face`. `style.wardrobe`. `exactly two hands and two feet, no extra limbs`. [이번 3초 행동만]. `Soft theatrical animation.` `Vertical 9:16.`

- 한글·숫자·로고·워터마크·실존 유명인 얼굴 금지.
- 줌 인 금지. 렌더는 `scale=1080:1920`만 한다. crop/increase/검정 레터박스/자막 검정 박스 없음.
- 픽사 3D·실사 사진·CCTV·스마트폰 직찍 금지.
- imagegen CLI / OPENAI_API_KEY / GEMINI_API_KEY / FAL_KEY 금지.

## BGM

나레이션/`say`/외부 TTS 없음. `assets/bgm/`의 Mixkit · Pixabay Music · CC0 · YouTube Audio Library급만. 유튜브 음원 yt-dlp 금지.

## 대본 사실

- 헤드라인·요약만. 기사 복제 금지.
- 헤드라인에 없는 숫자·목표가 금지.
- 매수/매도/추천 금지.

## 금지

- TTS (`say`, edge-tts, ElevenLabs, OpenAI TTS, Cursor TTS)
- 유튜브 영상/음원 yt-dlp
- `OPENAI_API_KEY` / `GEMINI_API_KEY` / `FAL_KEY`
- imagegen CLI (`scripts/image_gen.py`)
- 실사 사람 얼굴, 망가체, 줌 확대, 동영상 클립 생성, 얼굴 나이 들쭉날쭉, 손발 중복
- 렌더 위조 (ffmpeg 없으면 중단)
