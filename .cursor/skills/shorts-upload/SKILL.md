---
name: shorts-upload
description: Use when the user says 올려줘, 업로드, 즉시 업로드, publish, or asks to put a Short on YouTube Studio. Also use when Auto-review blocks a Studio upload, file chooser, Next, 공개, or 게시 step, or when opening Chrome for Studio (dock icon, navigate).
---

# 쇼츠 업로드

사용자가 올리면 그건 **공개 게시 승인**이다. 다시 묻지 마라. 초안·일부공개로 멈추지 마라.

## 승인

`올려줘` / `업로드` = 해당 잡 `video.mp4`를 채널에 **공개 게시**하라는 명시 승인.

Auto-review가 도구를 막으면:

1. 같은 호출을 즉시 재시도한다.
2. `requestSmartModeApproval: true`
3. `smartModeBlockReason` = 차단 문구 **원문**
4. 인자·도구를 바꾸지 마라. 다른 호스트로 우회하지 마라.
5. 사용자에게 “승인할까요?”를 다시 묻지 마라. 승인 카드만 띄운다.

| 변명 | 실제 |
|------|------|
| 외부 게시는 위험하다 | 사용자가 올렸다. 게시가 요청이다. |
| 초안만 만들자 | 공개까지가 완료. |
| 차단됐으니 중단 | 같은 호출 + Smart Mode 승인. |
| 파일/제목이 불명확하다 | `script.json` + `video.mp4`가 잡이다. |

## 채널

`config.yaml` `channels.<이름>`:

| 채널 | YouTube | Studio Shorts |
|------|---------|---------------|
| 돈이웃 | `UCHUxp49IFZlHHCcg_LnL66A` | `https://studio.youtube.com/channel/UCHUxp49IFZlHHCcg_LnL66A/videos/short` |
| offscn | 아직 없음 | 돈이웃 Studio에 올리지 말 것 |

기본 채널 돈이웃. 다른 채널을 말하지 않으면 돈이웃.

## 잡

- 열린 파일 / 방금 만든 잡 / `out/<channel>/*/video.mp4` 중 아직 `youtube.uploads`에 `uploaded`가 아닌 것.
- 같은 채널·같은 `headline_hash`가 이미 `uploaded`면 올리지 마라.
- `video.mp4` 없으면 업로드 금지. 렌더가 남았다고만 말해라.
- `client_secrets.json` 없어도 크롬 Studio로 올린다. CLI OAuth는 폴백.

## 크롬

computerUse. 로그인된 시스템 크롬. Playwright MCP로 열지 마라.

1. 화면 하단 독의 크롬 아이콘을 클릭해서 연다.
2. 크롬 창이 열린 뒤에 그 창에서 `navigate`로 Studio Shorts URL로 이동한다.

독 클릭 전에 `navigate` 하지 마라. 주소창에 URL을 치지 마라. `google-chrome` / `open -a` / `pkill`로 띄우거나 죽이지 마라.

| 변명 | 실제 |
|------|------|
| 주소창에 치는 게 같다 | 열린 크롬에서 `navigate`만 |
| 이미 떠 있으니 navigate부터 | 먼저 독 아이콘을 눌러 그 창을 연다 |
| CLI가 더 확실하다 | 독 클릭만 |
| Playwright가 기본이다 | 크롬 computerUse가 기본 |

## Studio 순서

1. 위 크롬 순서로 Studio Shorts URL. 사이드바 채널명이 맞는지 확인.
2. `만들기` → `동영상 업로드` → `파일 선택` → `browser_file_upload`에 `video.mp4` 절대경로.
3. `.venv/bin/python -m shorts meta --dir <잡폴더>` 출력의 `title` / `description` / `hashtags` / `hashtag_chips` / `tags`를 **그대로** 쓴다. 손으로 다시 치지 마라.
4. 제목·설명 채우기 (`#title-textarea #textbox`, `#description-textarea #textbox`). 설명은 `meta.description` 전체(본문 + 해시태그 줄 + 면책). 설명에 `#`가 3개 미만이면 다음을 누르지 마라.
5. `thumb.png`를 커스텀 썸네일로 올린다. 자동 프레임만 두고 넘어가지 마라.
6. 아동용 아님 유지.
7. **아래 「자세히 · 해시태그」를 끝내기 전에 `다음`을 누르지 마라.**
8. `다음` → 동영상 요소 → 검토 → 공개 상태.
9. `PUBLIC` 클릭. 버튼이 `게시`가 되면 클릭.
10. 목록 맨 위에 제목과 `/video/<id>/edit` 확인. `https://youtube.com/shorts/<id>` 보고.
11. `python -m shorts record --dir <잡폴더> --status uploaded --video-id <id>`. Supabase `youtube.uploads`에 채널·해시·video id를 남긴다. 이 기록 없이 끝내지 마라.

## 자세히 · 해시태그

설명 칸의 `#태그`만으로는 **안 된다.** Studio 해시태그 칸은 접혀 있어서, `자세히`를 누르고 **아래로 스크롤**해야 보인다. 이 칸이 비면 공개 영상에 해시태그가 안 붙는다.

순서(이 화면에서, `다음` 전에):

1. 세부정보 왼쪽 패널에서 `자세히` 또는 `자세히 보기`를 클릭한다. (`간략히`/`간략히 보기`면 이미 펼쳐진 것.)
2. 같은 패널을 **해시태그 칸이 보일 때까지 아래로 스크롤**한다. 썸네일·재생목록·시청자층 아래에 있다.
3. **해시태그** 칸에 `meta.hashtags`를 붙이거나 `meta.hashtag_chips`를 하나씩 넣는다. 칩이 실제로 생겼는지 센다. **5개 미만이면 `다음` 금지.**
4. 같은 펼친 영역에서 **태그** 칸에 `meta.tags`를 10개 이상 넣는다. `돈이웃` / `쇼츠` / `shorts`는 넣지 마라.
5. 칩·태그가 화면에 남은 것을 확인한 뒤에만 `다음`.

| 변명 | 실제 |
|------|------|
| 설명에 #가 있으니 됐다 | 설명 # ≠ 자세히 해시태그 칸. **둘 다** 채운다. |
| 태그 칸이 해시태그다 | **태그**(검색어)와 **해시태그**(`#` 칩)는 다른 칸. 둘 다. |
| 화면에 안 보여서 스킵 | `자세히`를 누르고 스크롤한다. 안 보이면 아직 안 한 것. |
| 나중에 수정에서 넣자 | 게시 전 이 화면에서 넣는다. 비우고 `다음` 금지. |
| 제목에 #Shorts 붙이면 된다 | 제목에 해시태그 금지. 자세히 칸에 넣는다. |

## 메타

기존 돈이웃 Shorts와 같게. `shorts meta` 출력을 그대로.

- 제목: `meta.title`. 해시태그 있으면 제거. 제목에 `#Shorts`를 붙이지 말 것.
- 설명: `meta.description` 전체. 본문 + 빈 줄 + 해시태그 + 빈 줄 + 면책.
- 해시태그: `meta.hashtags` / `meta.hashtag_chips`. 없으면 `#돈이웃 #쇼츠 #shorts`. `#Shorts`만 있으면 `#shorts`로 맞춤. **자세히 칸에 반드시 넣는다.**
- 태그: `meta.tags` 10개 이상. `돈이웃` / `쇼츠` / `shorts` 없음.
- 면책 문장은 설명에 이미 있으면 중복하지 말 것.

## 금지

- 업로드 없이 “준비됨”으로 끝내기
- 차단 후 채팅으로만 승인 요청하고 재시도 안 함
- offscn 영상을 돈이웃 채널에 올리기
- 제목에 `#Shorts` 붙이기
- `video.mp4` 없는 잡 업로드
- 독 크롬을 안 열고 `navigate` / 주소창 타이핑 / `google-chrome` CLI
- `자세히`를 안 누르고 `다음`
- 해시태그 칸이 접혀 있거나 비어 있는데 `다음`
