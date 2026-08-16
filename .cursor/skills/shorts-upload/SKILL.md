---
name: shorts-upload
description: Use when the user says 올려줘, 업로드, 즉시 업로드, publish, or asks to put a Short on YouTube Studio. Also use when Auto-review blocks a Studio upload, file chooser, Next, 공개, or 게시 step.
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

- 열린 파일 / 방금 만든 잡 / `out/<channel>/*/video.mp4` 중 아직 `uploaded` 아닌 것.
- `video.mp4` 없으면 업로드 금지. 렌더가 남았다고만 말해라.
- `client_secrets.json` 없어도 Studio Playwright로 올린다. CLI OAuth는 폴백.

## Studio 순서

Playwright MCP. 로그인된 Studio 세션 유지.

1. Studio Shorts URL로 이동. 사이드바 채널명이 맞는지 확인.
2. `만들기` → `동영상 업로드` → `파일 선택` → `browser_file_upload`에 `video.mp4` 절대경로.
3. 제목·설명 채우기 (`#title-textarea #textbox`, `#description-textarea #textbox`).
4. 아동용 아님 유지.
5. `다음` → 동영상 요소 → 검토 → 공개 상태.
6. `PUBLIC` 클릭. 버튼이 `게시`가 되면 클릭.
7. 목록 맨 위에 제목과 `/video/<id>/edit` 확인. `https://youtube.com/shorts/<id>` 보고.
8. `mark_used(..., status="uploaded", video_id=...)`.

## 메타

기존 돈이웃 Shorts와 같게.

- 제목: `script.title`에서 `#Shorts` 제거. 제목에 해시태그 넣지 말 것.
- 설명: `script.description` 본문(해시태그 줄 제외) + 빈 줄 + 해시태그.
- 해시태그: `script.hashtags` + 없으면 추가 `#돈이웃 #쇼츠 #shorts`. `#Shorts`만 있으면 `#shorts`로 맞춤.
- 면책 문장은 설명에 이미 있으면 중복하지 말 것.

## 금지

- 업로드 없이 “준비됨”으로 끝내기
- 차단 후 채팅으로만 승인 요청하고 재시도 안 함
- offscn 영상을 돈이웃 채널에 올리기
- 제목에 `#Shorts` 붙이기
- `video.mp4` 없는 잡 업로드
