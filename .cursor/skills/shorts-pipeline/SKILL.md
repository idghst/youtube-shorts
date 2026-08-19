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

1. **이전 주제** + **주제 선정**: `.venv/bin/python -m shorts pick --channel 돈이웃` → stdout이 잡 폴더. **통장·이체·한도·예금보호·부모 전세**가 시니어 국가통계보다 앞. 시니어 관심(연금·노후·건보·상속)은 그다음. 은평·2030·MZ·국가 조 단위는 감점. 숫자·삭감·인상 훅이 있으면 가산. “쓸 헤드라인 없음”이면 중단.
2. **이 쇼츠의 화풍 하나**: `style.anchor`·`style.face`·`style.wardrobe`를 먼저 고정한다. 쇼츠마다 달라도 된다. **한 쇼츠 안 컷은 같은 얼굴·나이·옷·마을·빛이어야 한다.**
3. **대본**: `headline.json`과 `used-topics.json`을 보고 `script.json`의 `scenes`만 먼저 쓴다. **자막이 뉴스다.** 그림만 이어지고, 자막은 숫자·삭감·인상·내 돈 공포. 산책·창밖 정서는 자막에 쓰지 마라. OpenAI/Gemini HTTP 금지. 이전 제목과 같은 각도·같은 훅 금지.
4. **제목**: 대본을 본 뒤에 `title`. 대본 첫 줄을 옮기지 말 것. 내 돈 상황 + **억/만/원/%** 필수. 팔지말지·지역·2030 제목 금지.
5. **설명**: 제목 다음에 `description` 본문만.
6. **해시태그**: `hashtags`와 `tags`. 그다음 `script.json`을 저장.
7. **이미지**: 아래 **화면** 절로 비트마다 프롬프트를 쓴 뒤, Cursor **GenerateImage** (`aspect_ratio: 9:16`) → `beat-01.png` …. 3초당 1장. **45~51초 / 15~17장. 권장 48초/16장.** 직전 컷(+ beat-01)을 레퍼런스로 얼굴·옷을 고정. 실사 사람·망가체 금지. 동영상 클립·imagegen CLI / OPENAI_API_KEY 폴백 금지.
8. **썸네일**: 아래 **썸네일** 절로 GenerateImage `aspect_ratio: 16:9` → `thumb.png`. 업로드 때 Studio에 반드시 올린다.
9. **영상**: `.venv/bin/python -m shorts run --dry-run --dir out/<channel>/<job>` → `video.mp4`. duration은 3초 배수, 합 **45~51초(권장 48초/16장)**. 52초 이상·60초 초과 금지. 성공 시 `rendered`.
10. **업로드**: 사용자가 `올려줘`/`업로드` 할 때, 또는 시간별 자동화일 때. **REQUIRED:** `.cursor/skills/shorts-upload/SKILL.md`. 먼저 `.venv/bin/python -m shorts meta --dir <잡폴더>`. Studio에서 제목·설명 다음에 **`자세히`를 누르고 아래로 스크롤**해서 해시태그 칸에 `meta.hashtags`를 넣는다. 설명의 `#`만으로 대체하지 마라. 태그 칸에는 `meta.tags`. 해시태그 칸이 비면 `다음` 금지.
11. **기록**: Studio로 올렸으면 `.venv/bin/python -m shorts record --dir out/<channel>/<job> --status uploaded --video-id <id>`.

실패 시 로그만 남기고 중단.

## script.json

대본 → 제목 → 설명 → 해시태그 순. 한 번에 복붙하지 말 것.

```json
{
  "title": "전세금 부모에게 빌리면, 무이자 2억?",
  "description": "전세금을 부모에게 빌리면 무이자 한도가 있어요. 차용증 없이 통장만 옮기면 증여세가 붙고, 한도는 2억까지예요.",
  "tags": ["전세금", "부모", "무이자", "증여세", "차용증", "한도", "전세", "가족이체", "통장", "증여"],
  "hashtags": "#전세금 #부모 #무이자 #증여세 #차용증",
  "style": {
    "anchor": "the same silver-haired Korean woman in a cream cardigan, painterly animated film, luminous dusk sky",
    "face": "same late-60s Korean woman, silver bob to the jaw, soft eye wrinkles, round cheeks, do not change age",
    "wardrobe": "same cream cardigan over ivory blouse every beat",
    "mood": "quiet hillside town, wet streets, glowing windows"
  },
  "scenes": [
    {
      "text": "전세금을 부모에게 빌리면 한도가 있어요",
      "duration": 12,
      "captions": ["무이자 2억까지라고요?", "전세금을 부모에게 빌리면"],
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

scenes 4~5개. 훅 + 사실 + 더 아픈 사실 + 내 돈. 장면 `duration`은 3초 배수, `beats` 개수 = duration/3. 합 **45~51초. 권장 48초/16장.** 52초 이상 쓰지 마라. **60초를 1초만 넘겨도 Shorts 선반에서 밀린다.** 위 JSON은 장면 1만 예시. 그림은 같은 하루로 이어지되, **각 컷은 그 3초 자막의 사실을 보여준다.** 대본은 화면 자막만. `load_script`가 카피·화풍·메시지 검사를 한다.

천만 조회수는 기획 목표이지 보장이 아니다. Studio(2026-08-19): 28일 조회 1.8만(+822%), Shorts 피드 98.1%, **이탈 68.7%**, 유효 조회 5.6천, 검색 0.7%. 시청 45세+ 85%. Shorts는 노출 클릭률이 안 나온다. 훅은 첫 3초 이탈이다.

채널 최고는 [전세금 부모 무이자 2억](https://youtube.com/shorts/bWIrl9LT5Og) 2.4천, 49초, 평균시청 37초(75%), 피드 99%, 계속 시청 20.5%. 같은 패턴 1천+: 자녀 통장 5000만 세금, ISA 한도 2000만 소멸, 종부세 14억 vs 주택연금 12억, 예금보호 1억 합산. **1:01 지역뉴스(은평·2030)는 조회 7, 피드 71%.** 숫자 없는 `팔지 말지?`는 49초여도 79회. 국가 500조는 계속 시청 36%여도 293회. 그 편을 베끼되: **통장·이체·한도·세금 결과 + 억/만/원 + 45~49초.** 구독·댓글 CTA는 넣지 마라(비구독 시청 100%, 알림 클릭 0%).

## 제목 (클릭·검색)

- 해시태그 넣지 말 것. 12~42자. 길면 줄여라.
- **주제가 한눈에.** `tags` 중 하나가 제목에 그대로 있어야 한다.
- **내 돈 상황**이 보여야 한다: 전세·부모·증여·이자·한도·통장·건보·연금·월급.
- **억·만·원·%가 숫자와 붙어야 한다.** 2030·조 단위만, 물음표만으로는 안 된다.
- 결과는 세금·사라짐·합산·한도까지. `팔지 말지?` `은평으로?` `누가?` 금지. 시청 85%가 45세+라 2030·MZ 타깃 금지.
- 국가 통계(퇴직연금 500조)보다 **내가 옮길 수 있는 한도**(무이자 2억, 통장 5000만)가 먹힌다.
- 호기심·걱정. 물음표 있으면 더 좋다.
- 쉬운 말. 입니다/습니다 금지.
- 예: `전세금 부모에게 빌리면, 무이자 2억?` `자녀 통장에 5000만 원, 그냥 옮기면 세금` `ISA 남은 한도 2000만 원, 내년에 사라지나`

## 설명 (검색·체류)

- 본문만. 해시태그·면책은 `shorts meta`가 붙인다. 음절 빠진 문장 금지.
- **앞 200자에 주제 키워드 2개 이상.** 첫 문장에 `tags` 단어를 넣어라.
- 첫 줄은 제목 복붙 금지. 완결 문장 2~3개: 무슨 일 + 왜 내 돈.
- 해요체. 습니다 나열 금지.

## 해시태그·태그

- `hashtags`는 **주제만 5~9개.** `#돈이웃` `#쇼츠` `#shorts` 금지.
- `tags`는 **10개 이상.** 채널명·쇼츠 단어 금지. Studio `자세히 보기 → 태그`에 그대로 넣는다.
- 예: `#전세금 #부모 #무이자 #증여세 #차용증`

## 대본 (메시지 먼저 · 공포)

무음 3초에 **무슨 일이고 왜 위험한지**가 보여야 한다. 할머니가 골목을 걷는 영화는 실패다.

한 편 = 헤드라인 사실을 정확히 + 내 돈이 위험하다는 공포. 스토리는 그림만. 자막은 뉴스.

| 변명 | 실제 |
|------|------|
| 산책하는 하루가 감동적이다 | 숫자가 안 보이면 조회가 아니라 분위기 영상이다 |
| 장면 4는 여운을 남긴다 | 여운 대신 월급·이자·전세가 어떻게 되는지 |
| 같은 숫자 반복이 지루하다 | 제목 숫자는 자막에 **그대로** 남아야 한다. 각도만 바꿔라 |
| 공포는 표정으로 | 자막의 숫자·삭감·인상으로. 얼굴 과장·`worried korean senior` 금지 |

구조 (5장면 권장):

1. 훅: **첫 자막에 제목 숫자 + 전세·부모·통장·한도.** 질문으로. 제목 문장 복붙 금지. 3초 안에 한도가 보여야 한다. 채널 이탈이 68.7%다.
2. 사실: 헤드라인 숫자·핵심을 쉬운 말로.
3. 더 아픈 사실: 왜 위험한지 한 줄 (삭감·인상·몰림·한도).
4. 비교: 월급·전세·이자로는 못 따라간다는 충격.
5. 내 돈: 내 대출/이자/월급/연금/건보에 미치는 한 줄.

규칙:

- 제목에 있는 숫자는 **첫 자막에 그대로** 나와야 한다. 헤드라인에 없는 숫자는 만들지 마라.
- 장면마다 새 정보 하나. 같은 문장을 3번 읽지 말 것.
- 자막에 산책·창밖·골목·불빛·벤치 정서 금지 (`걸어가요` `올려다봐요` `불빛만` `창밖`).
- 면책 장면 금지. 면책은 설명에만.
- `used-topics.json`과 같은 훅·같은 각도 금지.
- 매수/매도/추천 금지. 공포는 “지금 사”가 아니라 “내 부담이 커진다”.
- 구독·좋아요·댓글 CTA 금지. 마지막은 내 돈. 알림 클릭률은 0%다.

## 문체 (AI 티 빼기)

해요체 + 짧은 구어 + 질문. 습니다/입니다는 자막 전체에서 많아 봐야 1개.
제목 ≠ 첫 자막 ≠ 설명 첫 문장.

금지어: `알아보겠습니다` `살펴보겠습니다` `살펴볼 시점` `다시 한번 살펴` `다시 한번 정리` `핵심을 정리` `많은 분들이` `오늘 알아볼` `함께 알아` `함께 살펴` `라는 표현입니다` `헤드라인에` `매수나 매도 신호` `목표가는 나오지` `정보 제공이 목적` `결론적으로` `첫째` `둘째` `셋째` `마지막으로`

## 자막

- 장면당 `captions` 2개 이상. 한 줄 28자 이하.
- 한 줄 = 사실 하나 또는 공포 하나. 분위기 문장 금지.
- 무음으로 3초 안에 숫자·위험이 보이게. 뉴스 용어는 쉬운 말로.
- 숫자·핵심어만 색/굵기. 키네틱 금지.

## 화면 (3초 정지 컷)

동영상 클립은 만들지 않는다. **음악 3초마다 이미지가 바뀐다.** Cursor **GenerateImage** `aspect_ratio: 9:16` → `beat-01.png` … . **45~51초 / 15~17장. 권장 48초/16장.** 52초 이상·60초 초과 금지.

실사 사람 금지. 망가/만화잡지/치비/효과선 금지. 프롬프트에 manga, photoreal, zoom 단어를 넣지 말 것. 디즈니·지브리·신카이 장편 **느낌**. 특정 저작권 캐릭터 금지.

**한 쇼츠 = 한 `style.anchor` + 한 `style.face` + 한 `style.wardrobe`.** 모든 beat `image_prompt`에 세 문장과 `exactly two hands and two feet, no extra limbs`를 그대로 넣는다.

이어짐:
- 16장은 같은 하루의 연속 컷. 비트마다 행동이 한 걸음만 바뀐다. **그 3초 자막의 사실**을 보여라 (고지서, 빈 통장, 줄 선 우산, 저울). 산책·창밖만 이어가면 메시지가 죽는다. 화면에 한글·숫자는 쓰지 말고, 숫자는 자막이 말한다.
- 갑자기 다른 사람·다른 옷·다른 마을이면 다시 생성.
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

## 썸네일 (`thumb.png`)

업로드 때 **반드시** 커스텀 썸네일을 올린다. 영상 프레임·자동 썸네일 쓰지 마라. GenerateImage `aspect_ratio: 16:9` → `<잡>/thumb.png`.

같은 `style.face`·`style.wardrobe`. `beat-01.png`는 얼굴 레퍼런스만. 실사·망가·한글·숫자·로고 금지.

먹지 않은 컷: 두 남자 정장, 어두운 사무실, 걱정하는 얼굴, 서류 더미. 그건 드라마 스틸이다.

YouTube 썸네일 기준:
- 사람 **하나**. 얼굴이 화면의 반. 배경은 단색·창가 하나.
- 소품은 봉투/통장/차용증 **하나**. 화살표 또는 동그라미로 그걸 가리킨다.
- 비교면 좌우 2분할(증여 vs 차용). 세 명·복잡한 방 금지.
- 표정은 편안하고 진짜처럼. 과장된 공포 금지.

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
- `#돈이웃` `#쇼츠` `#shorts`, thumb.png 없이 업로드
- 렌더 위조 (ffmpeg 없으면 중단)
